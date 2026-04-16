"""
Trading Strategy Module
Implements various trading strategies including RSI, MACD, and ML-based signals
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class TechnicalIndicators:
    """Calculate technical indicators for trading"""
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD line, Signal line, and Histogram"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def moving_average(prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Volume Simple Moving Average"""
        return volume.rolling(window=period).mean()


class TradingStrategy:
    """Base trading strategy class"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate trading signal based on OHLCV data"""
        raise NotImplementedError("Subclasses must implement generate_signal")


class RSIStrategy(TradingStrategy):
    """RSI-based trading strategy"""
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        Generate signal based on RSI
        Returns: {'signal': 'BUY'|'SELL'|'HOLD', 'strength': 0-100, 'reason': str}
        """
        if df.empty or len(df) < self.rsi_period:
            return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
        
        rsi = TechnicalIndicators.rsi(df['close'], self.rsi_period)
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < self.rsi_oversold:
            strength = min(100, (self.rsi_oversold - current_rsi) * 2)
            return {
                'signal': 'BUY',
                'strength': strength,
                'reason': f'RSI oversold at {current_rsi:.2f}'
            }
        elif current_rsi > self.rsi_overbought:
            strength = min(100, (current_rsi - self.rsi_overbought) * 2)
            return {
                'signal': 'SELL',
                'strength': strength,
                'reason': f'RSI overbought at {current_rsi:.2f}'
            }
        else:
            return {
                'signal': 'HOLD',
                'strength': 50,
                'reason': f'RSI neutral at {current_rsi:.2f}'
            }


class MACDStrategy(TradingStrategy):
    """MACD-based trading strategy"""
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate signal based on MACD crossover"""
        if df.empty or len(df) < 30:
            return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
        
        macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'])
        
        # Check for bullish crossover (MACD crosses above signal)
        if macd_line.iloc[-2] < signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]:
            return {
                'signal': 'BUY',
                'strength': 75,
                'reason': 'MACD bullish crossover'
            }
        # Check for bearish crossover (MACD crosses below signal)
        elif macd_line.iloc[-2] > signal_line.iloc[-2] and macd_line.iloc[-1] < signal_line.iloc[-1]:
            return {
                'signal': 'SELL',
                'strength': 75,
                'reason': 'MACD bearish crossover'
            }
        else:
            return {
                'signal': 'HOLD',
                'strength': 50,
                'reason': 'No MACD crossover'
            }


class CombinedStrategy(TradingStrategy):
    """Combined strategy using multiple indicators"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.rsi_strategy = RSIStrategy(config)
        self.macd_strategy = MACDStrategy(config)
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate signal by combining multiple strategies"""
        if df.empty or len(df) < 30:
            return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
        
        rsi_signal = self.rsi_strategy.generate_signal(df)
        macd_signal = self.macd_strategy.generate_signal(df)
        
        # Calculate combined signal
        signals = [rsi_signal, macd_signal]
        buy_count = sum(1 for s in signals if s['signal'] == 'BUY')
        sell_count = sum(1 for s in signals if s['signal'] == 'SELL')
        
        avg_strength = sum(s['strength'] for s in signals) / len(signals)
        
        if buy_count >= 2:
            return {
                'signal': 'STRONG_BUY',
                'strength': avg_strength,
                'reason': f"Multiple indicators: {rsi_signal['reason']}, {macd_signal['reason']}"
            }
        elif buy_count == 1:
            return {
                'signal': 'BUY',
                'strength': avg_strength,
                'reason': f"RSI: {rsi_signal['reason']}, MACD: {macd_signal['reason']}"
            }
        elif sell_count >= 2:
            return {
                'signal': 'STRONG_SELL',
                'strength': avg_strength,
                'reason': f"Multiple indicators: {rsi_signal['reason']}, {macd_signal['reason']}"
            }
        elif sell_count == 1:
            return {
                'signal': 'SELL',
                'strength': avg_strength,
                'reason': f"RSI: {rsi_signal['reason']}, MACD: {macd_signal['reason']}"
            }
        else:
            return {
                'signal': 'HOLD',
                'strength': avg_strength,
                'reason': f"RSI: {rsi_signal['reason']}, MACD: {macd_signal['reason']}"
            }


class MLStrategy(TradingStrategy):
    """Machine Learning based strategy using Random Forest"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML model"""
        features = pd.DataFrame(index=df.index)
        
        # Price-based features
        features['returns'] = df['close'].pct_change()
        features['volatility'] = df['close'].rolling(window=10).std()
        
        # Technical indicators
        features['rsi'] = TechnicalIndicators.rsi(df['close'])
        macd, signal, hist = TechnicalIndicators.macd(df['close'])
        features['macd'] = macd
        features['macd_signal'] = signal
        features['macd_hist'] = hist
        
        # Moving averages
        features['sma_20'] = TechnicalIndicators.moving_average(df['close'], 20)
        features['ema_20'] = TechnicalIndicators.ema(df['close'], 20)
        features['price_sma_ratio'] = df['close'] / features['sma_20']
        
        # Volume features
        features['volume_sma'] = TechnicalIndicators.volume_sma(df['volume'], 20)
        features['volume_ratio'] = df['volume'] / features['volume_sma']
        
        # Lagged returns
        for i in range(1, 6):
            features[f'returns_lag_{i}'] = features['returns'].shift(i)
        
        features.dropna(inplace=True)
        return features
    
    def train(self, df: pd.DataFrame) -> bool:
        """Train the ML model on historical data"""
        try:
            features = self.prepare_features(df)
            
            # Create target: 1 if price goes up in next period, 0 otherwise
            target = (df['close'].shift(-1) > df['close']).astype(int)
            target = target.loc[features.index]
            
            # Scale features
            X = self.scaler.fit_transform(features)
            y = target.values
            
            # Train model
            self.model.fit(X, y)
            self.is_trained = True
            
            return True
        except Exception as e:
            print(f"Error training ML model: {e}")
            return False
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate signal using trained ML model"""
        if not self.is_trained:
            # Train on the fly if not trained
            if len(df) > 100:
                self.train(df)
            else:
                return {'signal': 'HOLD', 'strength': 0, 'reason': 'Model not trained, insufficient data'}
        
        try:
            features = self.prepare_features(df)
            X = self.scaler.transform(features.tail(1))
            
            prediction = self.model.predict(X)[0]
            probability = self.model.predict_proba(X)[0]
            
            if prediction == 1:
                strength = probability[1] * 100
                return {
                    'signal': 'BUY',
                    'strength': strength,
                    'reason': f'ML model predicts upward movement ({probability[1]*100:.1f}%)'
                }
            else:
                strength = probability[0] * 100
                return {
                    'signal': 'SELL',
                    'strength': strength,
                    'reason': f'ML model predicts downward movement ({probability[0]*100:.1f}%)'
                }
        except Exception as e:
            print(f"Error generating ML signal: {e}")
            return {'signal': 'HOLD', 'strength': 0, 'reason': f'Error: {str(e)}'}


def get_strategy(strategy_type: str, config: Dict) -> TradingStrategy:
    """Factory function to get strategy instance"""
    strategies = {
        'rsi': RSIStrategy,
        'macd': MACDStrategy,
        'combined': CombinedStrategy,
        'ml': MLStrategy
    }
    
    strategy_class = strategies.get(strategy_type.lower(), CombinedStrategy)
    return strategy_class(config)


if __name__ == "__main__":
    # Test strategies with sample data
    import json
    
    # Create sample OHLCV data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    prices = 50000 + np.cumsum(np.random.randn(100) * 100)
    volumes = np.random.randint(1000, 10000, 100)
    
    df = pd.DataFrame({
        'open': prices + np.random.randn(100) * 10,
        'high': prices + np.abs(np.random.randn(100) * 20),
        'low': prices - np.abs(np.random.randn(100) * 20),
        'close': prices,
        'volume': volumes
    }, index=dates)
    
    with open('config.example.json', 'r') as f:
        config = json.load(f)
    
    # Test RSI strategy
    rsi_strategy = RSIStrategy(config)
    signal = rsi_strategy.generate_signal(df)
    print(f"RSI Strategy: {signal}")
    
    # Test MACD strategy
    macd_strategy = MACDStrategy(config)
    signal = macd_strategy.generate_signal(df)
    print(f"MACD Strategy: {signal}")
    
    # Test Combined strategy
    combined_strategy = CombinedStrategy(config)
    signal = combined_strategy.generate_signal(df)
    print(f"Combined Strategy: {signal}")
    
    # Test ML strategy
    ml_strategy = MLStrategy(config)
    signal = ml_strategy.generate_signal(df)
    print(f"ML Strategy: {signal}")
