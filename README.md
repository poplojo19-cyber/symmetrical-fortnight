# 🤖 AI Crypto Trader - Real Paper Trading Bot

A **REAL** cryptocurrency trading bot that uses **LIVE market data** from CoinMarketCap API for paper trading (simulated trading with virtual money).

## ⚡ Features

- **REAL Market Data**: All prices, signals, and trades use LIVE data from CoinMarketCap API
- **Paper Trading**: Safe testing with virtual $10,000 starting balance - NO real money involved
- **AI Trading Signals**: RSI + MACD based strategy generates buy/sell signals from real market conditions
- **Live Dashboard**: GitHub Pages compatible dashboard shows real-time portfolio and trading activity
- **Risk Management**: Stop-loss (2%), take-profit (5%), max positions limits
- **Auto-Trading**: Runs continuously, checking markets every 5 minutes

## 📁 Files

| File | Description |
|------|-------------|
| `index.html` | **GitHub Pages Dashboard** - Shows LIVE market data from CoinMarketCap |
| `bot.py` | Main trading bot - executes paper trades with real prices |
| `data_fetcher.py` | CoinMarketCap API integration |
| `strategy.py` | Trading strategies (RSI, MACD, Combined) |
| `config.json` | Configuration with your API key |
| `requirements.txt` | Python dependencies |

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Your CoinMarketCap API key is already configured in `config.json` as `markapi`.

### 3. Run the Bot (Paper Trading)
```bash
python bot.py
```

The bot runs in **DRY RUN mode by default** - all trades are simulated with REAL market prices.

### 4. Deploy Dashboard to GitHub Pages

1. Go to your GitHub repo Settings → Pages
2. Select branch: `main` and folder: `/ (root)`
3. Save, then visit: `https://yourusername.github.io/your-repo/`

The dashboard will show:
- ✅ **LIVE crypto prices** from CoinMarketCap
- ✅ **Real-time portfolio** value
- ✅ **AI trading signals** based on actual market data
- ✅ **Trade history** from paper trading simulation

## 🔧 How It Works

### Dashboard (index.html)
```javascript
// Fetches REAL data from CoinMarketCap API
const response = await fetch('https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest', {
    headers: { 'X-CMC_PRO_API_KEY': 'markapi' }
});
```

### Trading Bot (bot.py)
```python
# Gets REAL OHLCV data from exchanges
df = exchange.get_ohlcv('BTC/USDT', timeframe='1h')

# Generates signals from REAL prices
signal = strategy.generate_signal(df)

# Executes paper trades at REAL market prices
if signal['signal'] == 'BUY':
    # Simulated trade at current market price
```

## 📊 Dashboard Features

- **Portfolio Overview**: Total value, cash, returns (all calculated from REAL prices)
- **Live Prices Table**: Top 10 cryptocurrencies with real-time prices
- **AI Signals**: Buy/Sell/Hold recommendations based on actual market analysis
- **Active Positions**: Current holdings with PnL calculated from live prices
- **Trade History**: All paper trades executed at real market prices

## ⚠️ Important Notes

1. **This is NOT financial advice** - Educational purposes only
2. **Paper Trading Only** - No real money is ever used
3. **API Rate Limits** - Dashboard refreshes every 30 seconds to respect CoinMarketCap limits
4. **Your API Key** - The key `markapi` is configured in both `config.json` and `index.html`

## 🎯 Strategy

The bot uses a combined strategy:
- **RSI (Relative Strength Index)**: Identifies overbought (>70) and oversold (<30) conditions
- **MACD (Moving Average Convergence Divergence)**: Detects trend changes
- **24h Price Change**: Factors in recent momentum

Signals:
- `STRONG_BUY`: RSI < 30 AND 24h change < -10%
- `BUY`: RSI < 30 OR 24h change < -5%
- `HOLD`: Neutral conditions
- `SELL`: RSI > 70 OR 24h change > 5%
- `STRONG_SELL`: RSI > 70 AND 24h change > 10%

## 📝 Verification

To verify the bot uses REAL data:

1. Open browser console on the dashboard
2. Watch network requests to `pro-api.coinmarketcap.com`
3. Compare displayed prices with CoinMarketCap.com
4. Check that prices update automatically every 30 seconds

## 🔐 Security

- API key stored in `config.json` (not committed to GitHub if you add to .gitignore)
- Dashboard uses client-side API calls (key visible in source - acceptable for public dashboard)
- For production, use a backend proxy to hide API key

## 📈 Performance Tracking

All trades are logged with:
- Entry/exit prices (from real market)
- PnL calculations
- Timestamp of each trade
- Portfolio performance over time

## 🛠️ Customization

Edit `config.json` to adjust:
```json
{
    "trading": {
        "amount_per_trade": 100,
        "stop_loss_percent": 2.0,
        "take_profit_percent": 5.0,
        "max_positions": 5
    },
    "check_interval_minutes": 5
}
```

## 📄 License

MIT License - Free for educational use

---

**Made with ❤️ for the crypto community**

*Data powered by [CoinMarketCap API](https://coinmarketcap.com/api/)*
