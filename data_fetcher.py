"""
Data Fetcher Module
Fetches cryptocurrency market data from CoinMarketCap and exchanges
"""

import requests
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class CoinMarketCapFetcher:
    """Fetch market data from CoinMarketCap API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }
    
    def get_top_cryptocurrencies(self, limit: int = 100) -> List[Dict]:
        """Get top cryptocurrencies by market cap"""
        try:
            response = requests.get(
                f"{self.base_url}/cryptocurrency/listings/latest",
                headers=self.headers,
                params={'limit': limit}
            )
            data = response.json()
            return data['data']
        except Exception as e:
            print(f"Error fetching from CoinMarketCap: {e}")
            return []
    
    def get_crypto_quotes(self, symbols: List[str]) -> Dict:
        """Get quotes for specific cryptocurrencies"""
        try:
            symbol_list = ','.join(symbols)
            response = requests.get(
                f"{self.base_url}/cryptocurrency/quotes/latest",
                headers=self.headers,
                params={'symbol': symbol_list}
            )
            data = response.json()
            return data['data']
        except Exception as e:
            print(f"Error fetching quotes: {e}")
            return {}
    
    def get_market_overview(self) -> Dict:
        """Get overall market metrics"""
        try:
            response = requests.get(
                f"{self.base_url}/global-metrics/quotes/latest",
                headers=self.headers
            )
            data = response.json()
            return data['data']
        except Exception as e:
            print(f"Error fetching market overview: {e}")
            return {}


class ExchangeFetcher:
    """Fetch OHLCV data from exchanges using CCXT"""
    
    def __init__(self, exchange_name: str = 'binance', api_key: str = None, secret: str = None):
        exchange_class = getattr(ccxt, exchange_name)
        config = {'enableRateLimit': True}
        if api_key and secret:
            config.update({'apiKey': api_key, 'secret': secret})
        self.exchange = exchange_class(config)
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Get OHLCV data for a symbol"""
        try:
            bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker price"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            print(f"Error fetching ticker for {symbol}: {e}")
            return {}
    
    def get_balance(self) -> Dict:
        """Get account balance (requires API keys)"""
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return {}
    
    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float = None) -> Dict:
        """Create a trading order"""
        try:
            if order_type == 'market':
                order = self.exchange.create_market_order(symbol, side, amount)
            else:
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            return order
        except Exception as e:
            print(f"Error creating order: {e}")
            return {}
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            print(f"Error fetching open orders: {e}")
            return []
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False


class DataAggregator:
    """Aggregate data from multiple sources"""
    
    def __init__(self, cmc_api_key: str, exchange_config: Dict = None):
        self.cmc = CoinMarketCapFetcher(cmc_api_key)
        if exchange_config:
            self.exchange = ExchangeFetcher(
                exchange_config.get('name', 'binance'),
                exchange_config.get('api_key'),
                exchange_config.get('secret')
            )
        else:
            self.exchange = ExchangeFetcher()
    
    def get_market_data(self, symbols: List[str], base_currency: str = 'USDT') -> Dict:
        """Get comprehensive market data for symbols"""
        data = {}
        
        # Get CMC data
        cmc_symbols = [s.replace(f'/{base_currency}', '') for s in symbols]
        cmc_data = self.cmc.get_crypto_quotes(cmc_symbols)
        
        # Get exchange OHLCV data
        for symbol in symbols:
            exchange_symbol = f"{symbol.replace('/', '')}/{base_currency}" if '/' not in symbol else symbol
            ohlcv = self.exchange.get_ohlcv(exchange_symbol)
            ticker = self.exchange.get_ticker(exchange_symbol)
            
            cmc_info = cmc_data.get(symbol.split('/')[0], {})
            
            data[symbol] = {
                'ohlcv': ohlcv,
                'ticker': ticker,
                'cmc_data': cmc_info,
                'last_updated': datetime.now().isoformat()
            }
        
        return data
    
    def get_portfolio_value(self, holdings: Dict[str, float], base_currency: str = 'USDT') -> float:
        """Calculate total portfolio value"""
        total = 0
        for symbol, amount in holdings.items():
            ticker = self.exchange.get_ticker(f"{symbol}/{base_currency}")
            if ticker and 'last' in ticker:
                total += amount * ticker['last']
        return total


if __name__ == "__main__":
    # Test the data fetcher
    import json
    
    with open('config.example.json', 'r') as f:
        config = json.load(f)
    
    aggregator = DataAggregator(
        config['coinmarketcap_api_key'],
        config.get('exchange')
    )
    
    # Test market data
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    data = aggregator.get_market_data(symbols)
    
    for symbol, info in data.items():
        print(f"\n{symbol}:")
        if info['ticker']:
            print(f"  Price: ${info['ticker'].get('last', 'N/A')}")
        if not info['ohlcv'].empty:
            print(f"  Close: ${info['ohlcv']['close'].iloc[-1]:.2f}")
            print(f"  Volume: {info['ohlcv']['volume'].iloc[-1]:.2f}")
