#!/usr/bin/env python3
"""
REAL AI Crypto Trading Bot - Paper Trading Mode
Uses FREE Binance public API (no key needed for market data)
Ready for live paper trading immediately
"""

import json
import time
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Load config
CONFIG_FILE = Path(__file__).parent / "config.json"
with open(CONFIG_FILE) as f:
    config = json.load(f)

# Initialize exchange (Binance public API - no key needed for market data)
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

class AITradingBot:
    def __init__(self):
        self.cash = config['initial_cash']
        self.holdings = {}
        self.trades = []
        self.dry_run = config.get('dry_run', True)
        self.coins = config['coins']
        self.amount_per_trade = config['trading']['amount_per_trade']
        
    def fetch_real_price(self, symbol):
        """Fetch REAL current price from Binance"""
        try:
            ticker = exchange.fetch_ticker(f"{symbol}/USDT")
            return ticker['last'], ticker
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None, None
    
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetch REAL candlestick data from Binance"""
        try:
            ohlcv = exchange.fetch_ohlcv(f"{symbol}/USDT", timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return None
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    def calculate_macd(self, prices):
        """Calculate MACD indicator"""
        series = pd.Series(prices)
        exp1 = series.ewm(span=12, adjust=False).mean()
        exp2 = series.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return macd.iloc[-1], signal.iloc[-1], histogram.iloc[-1]
    
    def generate_signal(self, symbol):
        """Generate BUY/SELL signal using REAL market data"""
        df = self.fetch_ohlcv(symbol)
        if df is None or len(df) < 50:
            return "HOLD", 50, "Insufficient data"
        
        closes = df['close'].values
        current_price = closes[-1]
        
        # Calculate indicators
        rsi = self.calculate_rsi(closes)
        macd, signal_line, histogram = self.calculate_macd(closes)
        
        # Calculate 24h change
        change_24h = ((closes[-1] - closes[-24]) / closes[-24]) * 100 if len(closes) >= 24 else 0
        
        # Generate signal
        score = 50
        reasons = []
        
        if rsi < 30:
            score += 25
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 70:
            score -= 25
            reasons.append(f"RSI overbought ({rsi:.1f})")
        
        if histogram > 0 and macd > signal_line:
            score += 20
            reasons.append("MACD bullish")
        elif histogram < 0 and macd < signal_line:
            score -= 20
            reasons.append("MACD bearish")
        
        if change_24h < -5:
            score += 15
            reasons.append(f"Down {change_24h:.1f}%")
        elif change_24h > 5:
            score -= 15
            reasons.append(f"Up {change_24h:.1f}%")
        
        # Determine signal
        if score >= 70:
            signal = "STRONG_BUY" if score >= 85 else "BUY"
        elif score <= 30:
            signal = "STRONG_SELL" if score <= 15 else "SELL"
        else:
            signal = "HOLD"
        
        reason = "; ".join(reasons) if reasons else "Neutral"
        return signal, min(max(score, 0), 100), f"{reason} | Price: ${current_price:.2f}"
    
    def execute_trade(self, symbol, signal, price):
        """Execute trade (paper or real)"""
        if signal not in ["BUY", "STRONG_BUY"] and signal not in ["SELL", "STRONG_SELL"]:
            return
        
        if signal in ["BUY", "STRONG_BUY"]:
            if self.cash >= self.amount_per_trade and symbol not in self.holdings:
                amount = self.amount_per_trade / price
                self.holdings[symbol] = {'amount': amount, 'avg_price': price}
                self.cash -= self.amount_per_trade
                self.trades.append({
                    'type': 'BUY',
                    'symbol': symbol,
                    'price': price,
                    'amount': amount,
                    'total': self.amount_per_trade,
                    'time': datetime.now().isoformat(),
                    'mode': 'PAPER' if self.dry_run else 'LIVE'
                })
                print(f"✅ {'[PAPER]' if self.dry_run else '[LIVE]'} BUY {symbol}: {amount:.6f} @ ${price:.2f}")
        
        elif signal in ["SELL", "STRONG_SELL"] and symbol in self.holdings:
            holding = self.holdings[symbol]
            total = holding['amount'] * price
            pnl = total - (holding['amount'] * holding['avg_price'])
            self.cash += total
            pnl_percent = (pnl / (holding['amount'] * holding['avg_price'])) * 100
            
            self.trades.append({
                'type': 'SELL',
                'symbol': symbol,
                'price': price,
                'amount': holding['amount'],
                'total': total,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'time': datetime.now().isoformat(),
                'mode': 'PAPER' if self.dry_run else 'LIVE'
            })
            
            print(f"✅ {'[PAPER]' if self.dry_run else '[LIVE]'} SELL {symbol}: {holding['amount']:.6f} @ ${price:.2f} | PnL: ${pnl:.2f} ({pnl_percent:.2f}%)")
            del self.holdings[symbol]
    
    def get_portfolio_value(self):
        """Calculate total portfolio value"""
        holdings_value = 0
        for symbol, holding in self.holdings.items():
            price, _ = self.fetch_real_price(symbol)
            if price:
                holdings_value += holding['amount'] * price
        
        total = self.cash + holdings_value
        initial = config['initial_cash']
        return {
            'cash': self.cash,
            'holdings_value': holdings_value,
            'total': total,
            'pnl': total - initial,
            'pnl_percent': ((total - initial) / initial) * 100
        }
    
    def run_once(self):
        """Run one trading cycle"""
        print(f"\n{'='*60}")
        print(f"🤖 AI Trading Bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'PAPER TRADING' if self.dry_run else 'LIVE TRADING'}")
        print(f"{'='*60}")
        
        signals = []
        for coin in self.coins:
            signal, strength, reason = self.generate_signal(coin)
            price, _ = self.fetch_real_price(coin)
            signals.append({'symbol': coin, 'signal': signal, 'strength': strength, 'reason': reason, 'price': price})
            print(f"{coin}: {signal} (strength: {strength:.0f}) - {reason}")
            
            # Execute trades for strong signals
            if price and strength >= 70:
                self.execute_trade(coin, signal, price)
        
        # Portfolio summary
        portfolio = self.get_portfolio_value()
        print(f"\n💰 Portfolio Summary:")
        print(f"   Cash: ${portfolio['cash']:.2f}")
        print(f"   Holdings: ${portfolio['holdings_value']:.2f}")
        print(f"   Total: ${portfolio['total']:.2f}")
        print(f"   PnL: ${portfolio['pnl']:.2f} ({portfolio['pnl_percent']:+.2f}%)")
        
        return signals, portfolio
    
    def run_continuous(self, interval_minutes=5):
        """Run bot continuously"""
        print(f"🚀 Starting AI Trading Bot in {'PAPER' if self.dry_run else 'LIVE'} mode...")
        print(f"Checking every {interval_minutes} minutes. Press Ctrl+C to stop.\n")
        
        try:
            while True:
                self.run_once()
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
            self.save_state()
    
    def save_state(self):
        """Save current state to file"""
        state = {
            'cash': self.cash,
            'holdings': self.holdings,
            'trades': self.trades,
            'last_update': datetime.now().isoformat()
        }
        with open(Path(__file__).parent / 'bot_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        print("💾 State saved to bot_state.json")

if __name__ == "__main__":
    bot = AITradingBot()
    
    # Load previous state if exists
    state_file = Path(__file__).parent / 'bot_state.json'
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        bot.cash = state.get('cash', bot.cash)
        bot.holdings = state.get('holdings', {})
        bot.trades = state.get('trades', [])
        print(f"📂 Loaded previous state from {state_file}")
    
    # Run once for testing, or use run_continuous() for 24/7 trading
    bot.run_once()
    # bot.run_continuous(interval_minutes=5)  # Uncomment for continuous trading
