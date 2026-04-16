"""
Main Trading Bot
Coordinates data fetching, strategy execution, and order management
"""

import json
import time
import schedule
from datetime import datetime
from typing import Dict, List, Optional
from data_fetcher import DataAggregator, ExchangeFetcher
from strategy import CombinedStrategy, get_strategy


class TradingBot:
    """Main trading bot class"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config = self.load_config(config_path)
        self.dry_run = self.config.get('dry_run', True)
        
        # Initialize data aggregator
        self.data = DataAggregator(
            self.config['coinmarketcap_api_key'],
            self.config.get('exchange')
        )
        
        # Initialize trading strategy
        self.strategy = CombinedStrategy(self.config.get('trading', {}))
        
        # Portfolio tracking
        self.portfolio = {
            'cash': self.config.get('initial_cash', 10000),
            'holdings': {},
            'trades': [],
            'performance': []
        }
        
        # Risk management
        self.trading_config = self.config.get('trading', {})
        self.stop_loss_pct = self.trading_config.get('stop_loss_percent', 2.0) / 100
        self.take_profit_pct = self.trading_config.get('take_profit_percent', 5.0) / 100
        self.amount_per_trade = self.trading_config.get('amount_per_trade', 100)
        self.max_positions = self.trading_config.get('max_positions', 5)
        
        print(f"Trading Bot initialized - {'DRY RUN MODE' if self.dry_run else 'LIVE MODE'}")
        print(f"Initial cash: ${self.portfolio['cash']:.2f}")
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_path} not found, using example config")
            with open('config.example.json', 'r') as f:
                return json.load(f)
    
    def check_signals(self) -> Dict[str, Dict]:
        """Check trading signals for all configured coins"""
        signals = {}
        coins = self.config.get('coins', ['BTC', 'ETH'])
        base_currency = self.trading_config.get('base_currency', 'USDT')
        
        for coin in coins:
            symbol = f"{coin}/{base_currency}"
            
            # Get OHLCV data
            df = self.data.exchange.get_ohlcv(symbol, timeframe='1h', limit=100)
            
            if df.empty:
                continue
            
            # Generate signal
            signal = self.strategy.generate_signal(df)
            current_price = df['close'].iloc[-1]
            
            signals[coin] = {
                'symbol': symbol,
                'price': current_price,
                'signal': signal['signal'],
                'strength': signal['strength'],
                'reason': signal['reason'],
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"{coin}: {signal['signal']} @ ${current_price:.2f} - {signal['reason']}")
        
        return signals
    
    def execute_trade(self, coin: str, signal: Dict) -> Optional[Dict]:
        """Execute a trade based on signal"""
        symbol = signal['symbol']
        current_price = signal['price']
        
        # Check if we should trade
        if signal['signal'] not in ['BUY', 'STRONG_BUY', 'SELL', 'STRONG_SELL']:
            return None
        
        # Check position limits
        if signal['signal'] in ['BUY', 'STRONG_BUY']:
            if len(self.portfolio['holdings']) >= self.max_positions:
                print(f"Max positions reached, skipping buy for {coin}")
                return None
            
            if self.portfolio['cash'] < self.amount_per_trade:
                print(f"Insufficient cash for buying {coin}")
                return None
            
            # Calculate amount to buy
            amount = self.amount_per_trade / current_price
            
            # Execute buy order
            if self.dry_run:
                # Simulate order
                order = {
                    'id': f"DRY_{len(self.portfolio['trades'])}",
                    'symbol': symbol,
                    'side': 'buy',
                    'amount': amount,
                    'price': current_price,
                    'status': 'filled',
                    'timestamp': datetime.now().isoformat()
                }
                
                # Update portfolio
                self.portfolio['cash'] -= self.amount_per_trade
                self.portfolio['holdings'][coin] = {
                    'amount': amount,
                    'avg_price': current_price,
                    'current_price': current_price
                }
            else:
                # Real order
                order = self.data.exchange.create_order(symbol, 'market', 'buy', amount)
                if order and order.get('status') == 'filled':
                    self.portfolio['holdings'][coin] = {
                        'amount': amount,
                        'avg_price': current_price,
                        'current_price': current_price
                    }
            
            self.portfolio['trades'].append(order)
            print(f"{'[DRY RUN] ' if self.dry_run else ''}BUY {amount:.6f} {coin} @ ${current_price:.2f}")
            return order
        
        elif signal['signal'] in ['SELL', 'STRONG_SELL']:
            if coin not in self.portfolio['holdings']:
                return None
            
            holding = self.portfolio['holdings'][coin]
            amount = holding['amount']
            
            # Execute sell order
            if self.dry_run:
                # Simulate order
                order = {
                    'id': f"DRY_{len(self.portfolio['trades'])}",
                    'symbol': symbol,
                    'side': 'sell',
                    'amount': amount,
                    'price': current_price,
                    'status': 'filled',
                    'timestamp': datetime.now().isoformat()
                }
                
                # Calculate profit/loss
                pnl = (current_price - holding['avg_price']) * amount
                pnl_percent = ((current_price - holding['avg_price']) / holding['avg_price']) * 100
                
                # Update portfolio
                self.portfolio['cash'] += amount * current_price
                del self.portfolio['holdings'][coin]
            else:
                # Real order
                order = self.data.exchange.create_order(symbol, 'market', 'sell', amount)
                if order and order.get('status') == 'filled':
                    pnl = (current_price - holding['avg_price']) * amount
                    pnl_percent = ((current_price - holding['avg_price']) / holding['avg_price']) * 100
                    del self.portfolio['holdings'][coin]
            
            self.portfolio['trades'].append(order)
            print(f"{'[DRY RUN] ' if self.dry_run else ''}SELL {amount:.6f} {coin} @ ${current_price:.2f} | PnL: ${pnl:.2f} ({pnl_percent:.2f}%)")
            return order
        
        return None
    
    def check_stop_loss_take_profit(self):
        """Check and execute stop-loss and take-profit orders"""
        base_currency = self.trading_config.get('base_currency', 'USDT')
        
        for coin, holding in list(self.portfolio['holdings'].items()):
            symbol = f"{coin}/{base_currency}"
            ticker = self.data.exchange.get_ticker(symbol)
            
            if not ticker or 'last' not in ticker:
                continue
            
            current_price = ticker['last']
            avg_price = holding['avg_price']
            
            # Check stop-loss
            if current_price <= avg_price * (1 - self.stop_loss_pct):
                print(f"Stop-loss triggered for {coin} at ${current_price:.2f}")
                self.execute_trade(coin, {
                    'symbol': symbol,
                    'price': current_price,
                    'signal': 'SELL',
                    'strength': 100,
                    'reason': 'Stop-loss'
                })
            
            # Check take-profit
            elif current_price >= avg_price * (1 + self.take_profit_pct):
                print(f"Take-profit triggered for {coin} at ${current_price:.2f}")
                self.execute_trade(coin, {
                    'symbol': symbol,
                    'price': current_price,
                    'signal': 'SELL',
                    'strength': 100,
                    'reason': 'Take-profit'
                })
    
    def update_portfolio_value(self) -> float:
        """Update current portfolio value"""
        base_currency = self.trading_config.get('base_currency', 'USDT')
        total_value = self.portfolio['cash']
        
        for coin, holding in self.portfolio['holdings'].items():
            symbol = f"{coin}/{base_currency}"
            ticker = self.data.exchange.get_ticker(symbol)
            
            if ticker and 'last' in ticker:
                current_price = ticker['last']
                holding['current_price'] = current_price
                total_value += holding['amount'] * current_price
        
        # Record performance
        self.portfolio['performance'].append({
            'timestamp': datetime.now().isoformat(),
            'total_value': total_value,
            'cash': self.portfolio['cash'],
            'holdings_count': len(self.portfolio['holdings']),
            'return_percent': ((total_value - self.config.get('initial_cash', 10000)) / self.config.get('initial_cash', 10000)) * 100
        })
        
        return total_value
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        total_value = self.update_portfolio_value()
        initial_cash = self.config.get('initial_cash', 10000)
        
        return {
            'total_value': total_value,
            'cash': self.portfolio['cash'],
            'holdings': self.portfolio['holdings'],
            'total_trades': len(self.portfolio['trades']),
            'return': total_value - initial_cash,
            'return_percent': ((total_value - initial_cash) / initial_cash) * 100,
            'last_updated': datetime.now().isoformat()
        }
    
    def run_once(self):
        """Run one iteration of the trading loop"""
        print(f"\n{'='*50}")
        print(f"Running trading cycle at {datetime.now().isoformat()}")
        print('='*50)
        
        # Check signals and execute trades
        signals = self.check_signals()
        
        for coin, signal in signals.items():
            if signal['signal'] in ['STRONG_BUY', 'BUY', 'STRONG_SELL', 'SELL']:
                self.execute_trade(coin, signal)
        
        # Check stop-loss and take-profit
        self.check_stop_loss_take_profit()
        
        # Update portfolio
        summary = self.get_portfolio_summary()
        print(f"\nPortfolio Value: ${summary['total_value']:.2f}")
        print(f"Return: ${summary['return']:.2f} ({summary['return_percent']:.2f}%)")
        print(f"Active Positions: {len(summary['holdings'])}")
    
    def run_continuous(self):
        """Run the bot continuously on a schedule"""
        interval = self.config.get('check_interval_minutes', 5)
        
        print(f"Starting continuous trading (checking every {interval} minutes)")
        print("Press Ctrl+C to stop")
        
        # Schedule the trading loop
        schedule.every(interval).minutes.do(self.run_once)
        
        # Run once immediately
        self.run_once()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def save_state(self, filename: str = 'bot_state.json'):
        """Save bot state to file"""
        state = {
            'portfolio': self.portfolio,
            'config': self.config,
            'last_updated': datetime.now().isoformat()
        }
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"State saved to {filename}")
    
    def load_state(self, filename: str = 'bot_state.json'):
        """Load bot state from file"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
                self.portfolio = state['portfolio']
                print(f"State loaded from {filename}")
                return True
        except FileNotFoundError:
            print(f"No saved state found at {filename}")
            return False


def main():
    """Main entry point"""
    import sys
    
    # Load configuration
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    
    # Create bot
    bot = TradingBot(config_path)
    
    # Try to load previous state
    bot.load_state()
    
    # Run mode selection
    if len(sys.argv) > 2 and sys.argv[2] == '--once':
        bot.run_once()
    else:
        bot.run_continuous()


if __name__ == "__main__":
    main()
