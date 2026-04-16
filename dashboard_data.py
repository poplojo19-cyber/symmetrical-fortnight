"""
Dashboard Data Exporter
Exports real trading data from the bot for the GitHub Pages dashboard
"""

import json
from datetime import datetime
from typing import Dict, List


class DashboardDataExporter:
    """Export trading data for the dashboard"""
    
    def __init__(self, bot=None):
        self.bot = bot
    
    def export_portfolio_data(self, portfolio_data: Dict) -> Dict:
        """Export portfolio data for dashboard"""
        return {
            'total_value': portfolio_data.get('total_value', 0),
            'cash': portfolio_data.get('cash', 0),
            'holdings': portfolio_data.get('holdings', {}),
            'total_trades': portfolio_data.get('total_trades', 0),
            'return': portfolio_data.get('return', 0),
            'return_percent': portfolio_data.get('return_percent', 0),
            'last_updated': datetime.now().isoformat()
        }
    
    def export_signals_data(self, signals: Dict) -> List[Dict]:
        """Export trading signals for dashboard"""
        exported_signals = []
        for coin, signal in signals.items():
            exported_signals.append({
                'coin': coin,
                'symbol': signal.get('symbol', ''),
                'price': signal.get('price', 0),
                'signal': signal.get('signal', 'HOLD'),
                'strength': signal.get('strength', 0),
                'reason': signal.get('reason', ''),
                'timestamp': signal.get('timestamp', datetime.now().isoformat())
            })
        return sorted(exported_signals, key=lambda x: x['strength'], reverse=True)
    
    def export_trade_history(self, trades: List[Dict]) -> List[Dict]:
        """Export trade history for dashboard"""
        exported_trades = []
        for trade in trades[-20:]:  # Last 20 trades
            exported_trades.append({
                'id': trade.get('id', ''),
                'symbol': trade.get('symbol', ''),
                'side': trade.get('side', ''),
                'amount': trade.get('amount', 0),
                'price': trade.get('price', 0),
                'total': trade.get('amount', 0) * trade.get('price', 0),
                'status': trade.get('status', ''),
                'timestamp': trade.get('timestamp', '')
            })
        return exported_trades
    
    def export_full_dashboard_data(self, portfolio: Dict, signals: Dict, trades: List[Dict], market_overview: Dict = None) -> Dict:
        """Export complete dashboard data"""
        return {
            'portfolio': self.export_portfolio_data(portfolio),
            'signals': self.export_signals_data(signals),
            'trade_history': self.export_trade_history(trades),
            'market_overview': market_overview or {},
            'last_updated': datetime.now().isoformat(),
            'is_live': True
        }
    
    def save_to_json(self, data: Dict, filename: str = 'dashboard_data.json'):
        """Save dashboard data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Dashboard data saved to {filename}")
    
    def load_from_json(self, filename: str = 'dashboard_data.json') -> Dict:
        """Load dashboard data from JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}


if __name__ == "__main__":
    # Test the exporter
    exporter = DashboardDataExporter()
    
    test_data = {
        'total_value': 10500.00,
        'cash': 5000.00,
        'holdings': {'BTC': {'amount': 0.05, 'avg_price': 60000, 'current_price': 62000}},
        'total_trades': 10,
        'return': 500.00,
        'return_percent': 5.0
    }
    
    exported = exporter.export_portfolio_data(test_data)
    exporter.save_to_json({'portfolio': exported})
    print("Test export completed")
