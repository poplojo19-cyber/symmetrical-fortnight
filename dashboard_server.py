"""
Dashboard Server
Flask-based web server for real-time trading dashboard
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from data_fetcher import DataAggregator, CoinMarketCapFetcher
from strategy import CombinedStrategy
from bot import TradingBot

app = Flask(__name__)

# Global bot instance (will be initialized on first request)
bot = None
last_update = None


def get_bot():
    """Get or initialize bot instance"""
    global bot, last_update
    
    if bot is None:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            with open('config.example.json', 'r') as f:
                config = json.load(f)
        
        bot = TradingBot(config)
        last_update = datetime.now()
    
    return bot


@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/status')
def api_status():
    """Get bot status"""
    try:
        bot_instance = get_bot()
        summary = bot_instance.get_portfolio_summary()
        
        return jsonify({
            'status': 'running',
            'dry_run': bot_instance.dry_run,
            'portfolio': summary,
            'last_update': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/signals')
def api_signals():
    """Get current trading signals"""
    try:
        bot_instance = get_bot()
        signals = bot_instance.check_signals()
        
        return jsonify({
            'signals': signals,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/market')
def api_market():
    """Get market overview from CoinMarketCap"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        with open('config.example.json', 'r') as f:
            config = json.load(f)
        
        cmc = CoinMarketCapFetcher(config['coinmarketcap_api_key'])
        overview = cmc.get_market_overview()
        top_cryptos = cmc.get_top_cryptocurrencies(limit=20)
        
        return jsonify({
            'overview': overview,
            'top_cryptocurrencies': top_cryptos,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades')
def api_trades():
    """Get trade history"""
    try:
        bot_instance = get_bot()
        
        return jsonify({
            'trades': bot_instance.portfolio['trades'][-50:],  # Last 50 trades
            'total_trades': len(bot_instance.portfolio['trades']),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/performance')
def api_performance():
    """Get portfolio performance history"""
    try:
        bot_instance = get_bot()
        
        return jsonify({
            'performance': bot_instance.portfolio['performance'][-100:],  # Last 100 data points
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Get or update configuration"""
    if request.method == 'POST':
        try:
            new_config = request.json
            with open('config.json', 'w') as f:
                json.dump(new_config, f, indent=2)
            return jsonify({'status': 'success', 'message': 'Configuration updated'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            with open('config.example.json', 'r') as f:
                config = json.load(f)
        
        # Hide sensitive data
        safe_config = config.copy()
        if 'coinmarketcap_api_key' in safe_config:
            safe_config['coinmarketcap_api_key'] = safe_config['coinmarketcap_api_key'][:8] + '...'
        if 'exchange' in safe_config:
            safe_config['exchange']['api_key'] = safe_config['exchange'].get('api_key', '')[:8] + '...'
            safe_config['exchange']['secret'] = '***'
        
        return jsonify(safe_config)


# Dashboard HTML Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Crypto Trader Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .status-running {
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
        }
        
        .status-dry-run {
            background: rgba(255, 193, 7, 0.2);
            color: #ffc107;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #00d9ff;
        }
        
        .metric {
            margin-bottom: 15px;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #888;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .positive {
            color: #00ff88;
        }
        
        .negative {
            color: #ff4757;
        }
        
        .signal-card {
            background: rgba(0, 217, 255, 0.1);
            border-left: 4px solid #00d9ff;
        }
        
        .signal-buy {
            background: rgba(0, 255, 136, 0.1);
            border-left-color: #00ff88;
        }
        
        .signal-sell {
            background: rgba(255, 71, 87, 0.1);
            border-left-color: #ff4757;
        }
        
        .signal-hold {
            background: rgba(255, 193, 7, 0.1);
            border-left-color: #ffc107;
        }
        
        .signal-strength {
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
        }
        
        .signal-strength-bar {
            height: 100%;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        th {
            color: #00d9ff;
            font-weight: 600;
        }
        
        tr:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            border: none;
            color: #1a1a2e;
            font-size: 1.5em;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0, 217, 255, 0.4);
            transition: transform 0.3s ease;
        }
        
        .refresh-btn:hover {
            transform: scale(1.1) rotate(180deg);
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #888;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        .chart-container {
            height: 300px;
            margin-top: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            padding: 20px;
        }
        
        footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 AI Crypto Trader</h1>
            <p>Real-time Trading Dashboard</p>
            <div style="margin-top: 15px;">
                <span id="statusBadge" class="status-badge status-running">Loading...</span>
                <span id="lastUpdate" style="margin-left: 15px; color: #888;"></span>
            </div>
        </header>
        
        <div class="grid">
            <!-- Portfolio Value -->
            <div class="card">
                <h2>💰 Portfolio Value</h2>
                <div class="metric">
                    <div class="metric-label">Total Value</div>
                    <div id="totalValue" class="metric-value">$0.00</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Cash Available</div>
                    <div id="cashValue" class="metric-value">$0.00</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Return</div>
                    <div id="returnValue" class="metric-value">$0.00 (0.00%)</div>
                </div>
            </div>
            
            <!-- Active Positions -->
            <div class="card">
                <h2>📊 Active Positions</h2>
                <div id="activePositions">
                    <div class="loading">Loading positions...</div>
                </div>
            </div>
            
            <!-- Trading Signals -->
            <div class="card signal-card">
                <h2>📈 Trading Signals</h2>
                <div id="tradingSignals">
                    <div class="loading">Loading signals...</div>
                </div>
            </div>
            
            <!-- Trade History -->
            <div class="card" style="grid-column: span 2;">
                <h2>📜 Recent Trades</h2>
                <div id="tradeHistory">
                    <div class="loading">Loading trades...</div>
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()" title="Refresh">🔄</button>
        
        <footer>
            <p>⚠️ This bot is for educational purposes only. Cryptocurrency trading involves significant risk.</p>
            <p>Powered by CoinMarketCap API & CCXT</p>
        </footer>
    </div>
    
    <script>
        let autoRefreshInterval;
        
        async function fetchAPI(endpoint) {
            try {
                const response = await fetch(`/api${endpoint}`);
                return await response.json();
            } catch (error) {
                console.error(`Error fetching ${endpoint}:`, error);
                return null;
            }
        }
        
        function formatCurrency(value) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(value);
        }
        
        function formatDateTime(isoString) {
            if (!isoString) return 'N/A';
            return new Date(isoString).toLocaleString();
        }
        
        function updateStatus(data) {
            const badge = document.getElementById('statusBadge');
            if (data.status === 'running') {
                badge.textContent = data.dry_run ? '🔸 DRY RUN MODE' : '🟢 LIVE MODE';
                badge.className = `status-badge ${data.dry_run ? 'status-dry-run' : 'status-running'}`;
            } else {
                badge.textContent = '❌ Error';
                badge.className = 'status-badge';
                badge.style.background = 'rgba(255, 71, 87, 0.2)';
                badge.style.color = '#ff4757';
            }
            
            document.getElementById('lastUpdate').textContent = 
                `Last update: ${formatDateTime(data.last_update)}`;
        }
        
        function updatePortfolio(data) {
            const portfolio = data.portfolio;
            
            document.getElementById('totalValue').textContent = formatCurrency(portfolio.total_value);
            document.getElementById('cashValue').textContent = formatCurrency(portfolio.cash);
            
            const returnEl = document.getElementById('returnValue');
            returnEl.textContent = `${formatCurrency(portfolio.return)} (${portfolio.return_percent.toFixed(2)}%)`;
            returnEl.className = `metric-value ${portfolio.return >= 0 ? 'positive' : 'negative'}`;
            
            // Update active positions
            const positionsEl = document.getElementById('activePositions');
            const holdings = portfolio.holdings;
            
            if (Object.keys(holdings).length === 0) {
                positionsEl.innerHTML = '<div style="color: #888; text-align: center; padding: 20px;">No active positions</div>';
            } else {
                let html = '<table><thead><tr><th>Coin</th><th>Amount</th><th>Avg Price</th><th>Current</th><th>PnL</th></tr></thead><tbody>';
                
                for (const [coin, holding] of Object.entries(holdings)) {
                    const pnl = (holding.current_price - holding.avg_price) * holding.amount;
                    const pnlPercent = ((holding.current_price - holding.avg_price) / holding.avg_price) * 100;
                    
                    html += `<tr>
                        <td>${coin}</td>
                        <td>${holding.amount.toFixed(6)}</td>
                        <td>${formatCurrency(holding.avg_price)}</td>
                        <td>${formatCurrency(holding.current_price)}</td>
                        <td class="${pnl >= 0 ? 'positive' : 'negative'}">
                            ${formatCurrency(pnl)} (${pnlPercent.toFixed(2)}%)
                        </td>
                    </tr>`;
                }
                
                html += '</tbody></table>';
                positionsEl.innerHTML = html;
            }
        }
        
        function updateSignals(data) {
            const signalsEl = document.getElementById('tradingSignals');
            const signals = data.signals;
            
            if (!signals || Object.keys(signals).length === 0) {
                signalsEl.innerHTML = '<div style="color: #888; text-align: center; padding: 20px;">No signals available</div>';
                return;
            }
            
            let html = '';
            for (const [coin, signal] of Object.entries(signals)) {
                const signalClass = signal.signal.includes('BUY') ? 'signal-buy' : 
                                   signal.signal.includes('SELL') ? 'signal-sell' : 'signal-hold';
                
                html += `<div class="card ${signalClass}" style="margin-bottom: 15px; padding: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>${coin}</strong>
                        <span style="font-size: 1.2em;">${signal.signal}</span>
                    </div>
                    <div style="color: #888; font-size: 0.9em; margin-top: 5px;">${signal.reason}</div>
                    <div style="font-size: 0.85em; margin-top: 5px;">Price: ${formatCurrency(signal.price)}</div>
                    <div class="signal-strength">
                        <div class="signal-strength-bar" style="width: ${signal.strength}%"></div>
                    </div>
                    <div style="font-size: 0.8em; color: #888; margin-top: 5px;">Strength: ${signal.strength.toFixed(0)}%</div>
                </div>`;
            }
            
            signalsEl.innerHTML = html;
        }
        
        function updateTrades(data) {
            const tradesEl = document.getElementById('tradeHistory');
            const trades = data.trades.slice(-10).reverse();  // Last 10 trades
            
            if (trades.length === 0) {
                tradesEl.innerHTML = '<div style="color: #888; text-align: center; padding: 20px;">No trades yet</div>';
                return;
            }
            
            let html = '<table><thead><tr><th>Type</th><th>Coin</th><th>Price</th><th>Amount</th><th>Time</th></tr></thead><tbody>';
            
            for (const trade of trades) {
                const coin = trade.symbol.split('/')[0];
                const typeClass = trade.side === 'buy' ? 'positive' : 'negative';
                
                html += `<tr>
                    <td class="${typeClass}"><strong>${trade.side.toUpperCase()}</strong></td>
                    <td>${coin}</td>
                    <td>${formatCurrency(trade.price)}</td>
                    <td>${trade.amount.toFixed(6)}</td>
                    <td>${formatDateTime(trade.timestamp)}</td>
                </tr>`;
            }
            
            html += '</tbody></table>';
            tradesEl.innerHTML = html;
        }
        
        async function refreshData() {
            console.log('Refreshing data...');
            
            // Fetch all data
            const [statusData, signalsData, tradesData] = await Promise.all([
                fetchAPI('/status'),
                fetchAPI('/signals'),
                fetchAPI('/trades')
            ]);
            
            if (statusData) {
                updateStatus(statusData);
                updatePortfolio(statusData);
            }
            
            if (signalsData) {
                updateSignals(signalsData);
            }
            
            if (tradesData) {
                updateTrades(tradesData);
            }
        }
        
        // Initial load
        refreshData();
        
        // Auto-refresh every 10 seconds
        autoRefreshInterval = setInterval(refreshData, 10000);
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            clearInterval(autoRefreshInterval);
        });
    </script>
</body>
</html>
'''


def main():
    """Run the dashboard server"""
    print("Starting AI Crypto Trader Dashboard...")
    print("Access the dashboard at: http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=8000, debug=False)


if __name__ == "__main__":
    main()
