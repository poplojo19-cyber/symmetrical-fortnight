"""
Backtesting Module
Test trading strategies on historical data
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from strategy import CombinedStrategy, RSIStrategy, MACDStrategy


class BacktestEngine:
    """Backtest trading strategies on historical data"""
    
    def __init__(self, config: Dict, initial_capital: float = 10000):
        self.config = config
        self.initial_capital = initial_capital
        self.trading_config = config.get('trading', {})
        
        # Initialize strategy
        self.strategy = CombinedStrategy(self.trading_config)
        
        # Risk management
        self.stop_loss_pct = self.trading_config.get('stop_loss_percent', 2.0) / 100
        self.take_profit_pct = self.trading_config.get('take_profit_percent', 5.0) / 100
        self.amount_per_trade = self.trading_config.get('amount_per_trade', 100)
    
    def run_backtest(self, df: pd.DataFrame, symbol: str = 'BTC/USDT') -> Dict:
        """
        Run backtest on historical OHLCV data
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading pair symbol
        
        Returns:
            Dictionary with backtest results
        """
        if df.empty or len(df) < 50:
            return {'error': 'Insufficient data for backtest'}
        
        # Initialize portfolio
        cash = self.initial_capital
        holdings = {}
        trades = []
        portfolio_values = []
        
        # Iterate through data (skip first 30 rows for indicator calculation)
        for i in range(30, len(df)):
            current_time = df.index[i]
            current_price = df['close'].iloc[i]
            
            # Get historical data up to this point
            historical_df = df.iloc[:i+1].copy()
            
            # Generate signal
            signal = self.strategy.generate_signal(historical_df)
            
            # Check existing positions for stop-loss/take-profit
            for coin in list(holdings.keys()):
                holding = holdings[coin]
                
                # Stop-loss
                if current_price <= holding['avg_price'] * (1 - self.stop_loss_pct):
                    pnl = (current_price - holding['avg_price']) * holding['amount']
                    cash += holding['amount'] * current_price
                    
                    trades.append({
                        'type': 'SELL',
                        'timestamp': current_time.isoformat(),
                        'price': current_price,
                        'amount': holding['amount'],
                        'pnl': pnl,
                        'reason': 'Stop-loss'
                    })
                    
                    del holdings[coin]
                
                # Take-profit
                elif current_price >= holding['avg_price'] * (1 + self.take_profit_pct):
                    pnl = (current_price - holding['avg_price']) * holding['amount']
                    cash += holding['amount'] * current_price
                    
                    trades.append({
                        'type': 'SELL',
                        'timestamp': current_time.isoformat(),
                        'price': current_price,
                        'amount': holding['amount'],
                        'pnl': pnl,
                        'reason': 'Take-profit'
                    })
                    
                    del holdings[coin]
            
            # Execute new trades based on signal
            if signal['signal'] in ['BUY', 'STRONG_BUY'] and len(holdings) < self.trading_config.get('max_positions', 5):
                if cash >= self.amount_per_trade:
                    amount = self.amount_per_trade / current_price
                    
                    holdings[symbol.split('/')[0]] = {
                        'amount': amount,
                        'avg_price': current_price,
                        'entry_time': current_time
                    }
                    
                    cash -= self.amount_per_trade
                    
                    trades.append({
                        'type': 'BUY',
                        'timestamp': current_time.isoformat(),
                        'price': current_price,
                        'amount': amount,
                        'reason': signal['reason']
                    })
            
            elif signal['signal'] in ['SELL', 'STRONG_SELL']:
                base_coin = symbol.split('/')[0]
                if base_coin in holdings:
                    holding = holdings[base_coin]
                    pnl = (current_price - holding['avg_price']) * holding['amount']
                    cash += holding['amount'] * current_price
                    
                    trades.append({
                        'type': 'SELL',
                        'timestamp': current_time.isoformat(),
                        'price': current_price,
                        'amount': holding['amount'],
                        'pnl': pnl,
                        'reason': signal['reason']
                    })
                    
                    del holdings[base_coin]
            
            # Calculate portfolio value
            total_value = cash
            for coin, holding in holdings.items():
                total_value += holding['amount'] * current_price
            
            portfolio_values.append({
                'timestamp': current_time.isoformat(),
                'value': total_value,
                'cash': cash,
                'holdings_value': total_value - cash
            })
        
        # Final portfolio value
        final_price = df['close'].iloc[-1]
        final_value = cash
        for coin, holding in holdings.items():
            final_value += holding['amount'] * final_price
        
        # Calculate metrics
        returns = [(pv['value'] / self.initial_capital - 1) * 100 for pv in portfolio_values]
        
        # Convert to DataFrame for analysis
        portfolio_df = pd.DataFrame(portfolio_values)
        portfolio_df.set_index('timestamp', inplace=True)
        
        # Calculate drawdown
        peak = portfolio_df['value'].cummax()
        drawdown = (portfolio_df['value'] - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # Calculate Sharpe ratio (simplified)
        daily_returns = portfolio_df['value'].pct_change().dropna()
        sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std() if daily_returns.std() > 0 else 0
        
        # Count winning/losing trades
        sell_trades = [t for t in trades if t['type'] == 'SELL' and 'pnl' in t]
        winning_trades = sum(1 for t in sell_trades if t['pnl'] > 0)
        losing_trades = sum(1 for t in sell_trades if t['pnl'] <= 0)
        
        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0
        
        return {
            'symbol': symbol,
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': final_value - self.initial_capital,
            'return_percent': (final_value / self.initial_capital - 1) * 100,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(trades),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'trades': trades,
            'portfolio_history': portfolio_values,
            'start_date': df.index[0].isoformat(),
            'end_date': df.index[-1].isoformat(),
            'data_points': len(df)
        }
    
    def compare_strategies(self, df: pd.DataFrame, symbols: List[str] = None) -> Dict:
        """Compare different strategies"""
        if symbols is None:
            symbols = ['BTC/USDT']
        
        results = {}
        
        # Test different strategy configurations
        strategies = [
            ('RSI Conservative', {'rsi_oversold': 25, 'rsi_overbought': 75}),
            ('RSI Aggressive', {'rsi_oversold': 35, 'rsi_overbought': 65}),
            ('Combined Default', {}),
        ]
        
        for strat_name, strat_config in strategies:
            config_copy = self.config.copy()
            config_copy['trading'] = {**self.trading_config, **strat_config}
            
            engine = BacktestEngine(config_copy, self.initial_capital)
            
            for symbol in symbols:
                result = engine.run_backtest(df, symbol)
                key = f"{strat_name}_{symbol}"
                results[key] = result
        
        return results


def generate_sample_data(days: int = 90, start_price: float = 50000) -> pd.DataFrame:
    """Generate sample OHLCV data for testing"""
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=days*24, freq='1h')
    
    # Generate realistic price movement with trend
    trend = np.linspace(0, 5000, days*24)
    noise = np.cumsum(np.random.randn(days*24) * 200)
    prices = start_price + trend + noise
    
    # Ensure positive prices
    prices = np.maximum(prices, 1000)
    
    # Generate OHLCV
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        volatility = abs(np.random.randn() * 50)
        open_price = price + np.random.randn() * 20
        high_price = max(open_price, price) + volatility
        low_price = min(open_price, price) - volatility
        close_price = price
        volume = np.random.randint(1000, 50000)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    return df


def main():
    """Run backtest example"""
    print("Loading configuration...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("config.json not found, using example config")
        with open('config.example.json', 'r') as f:
            config = json.load(f)
    
    print("Generating sample data...")
    df = generate_sample_data(days=90, start_price=50000)
    
    print(f"Data shape: {df.shape}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    
    print("\nRunning backtest...")
    engine = BacktestEngine(config, initial_capital=10000)
    results = engine.run_backtest(df, 'BTC/USDT')
    
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Symbol: {results['symbol']}")
    print(f"Period: {results['start_date']} to {results['end_date']}")
    print(f"Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"Final Value: ${results['final_value']:,.2f}")
    print(f"Total Return: ${results['total_return']:,.2f} ({results['return_percent']:.2f}%)")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print("="*50)
    
    # Show last 5 trades
    print("\nLast 5 Trades:")
    for trade in results['trades'][-5:]:
        if 'pnl' in trade:
            print(f"  {trade['type']} @ ${trade['price']:.2f} | PnL: ${trade['pnl']:.2f} ({trade['reason']})")
        else:
            print(f"  {trade['type']} @ ${trade['price']:.2f} ({trade['reason']})")
    
    # Save results
    with open('backtest_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("\nResults saved to backtest_results.json")


if __name__ == "__main__":
    main()
