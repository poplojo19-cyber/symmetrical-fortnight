# symmetrical-fortnight

# AI Crypto Trader Bot

A real cryptocurrency trading bot with AI-driven signals and a web dashboard.

## Features

- **Real-time Market Data**: Fetches data from CoinMarketCap API
- **Trading Strategy**: RSI-based trading with machine learning enhancements
- **Multi-Exchange Support**: Built on CCXT library (Binance, Coinbase, Kraken, etc.)
- **Web Dashboard**: Real-time portfolio tracking and trading signals
- **Backtesting**: Test strategies on historical data
- **Risk Management**: Stop-loss, take-profit, and position sizing

## ⚠️ Disclaimer

**This bot is for educational purposes only. Cryptocurrency trading involves significant risk. You can lose money. Never trade with money you cannot afford to lose.**

## Requirements

- Python 3.8+
- CoinMarketCap API key (get free at https://pro.coinmarketcap.com/)
- Exchange API keys (optional, for live trading)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `config.example.json` to `config.json`
2. Add your API keys:

```json
{
    "coinmarketcap_api_key": "YOUR_CMC_API_KEY",
    "exchange": {
        "name": "binance",
        "api_key": "YOUR_EXCHANGE_API_KEY",
        "secret": "YOUR_EXCHANGE_SECRET"
    },
    "trading": {
        "base_currency": "USDT",
        "amount_per_trade": 100,
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70
    }
}
```

## Usage

### Run the Trading Bot

```bash
python bot.py
```

### Run the Dashboard Server

```bash
python dashboard_server.py
```

Then open http://localhost:8000 in your browser.

### Backtest Strategy

```bash
python backtest.py
```

## Project Structure

```
├── bot.py              # Main trading bot logic
├── dashboard_server.py # Web dashboard server
├── index.html          # GitHub Pages dashboard
├── strategy.py         # Trading strategies (RSI, MACD, ML)
├── data_fetcher.py     # CoinMarketCap API integration
├── backtest.py         # Strategy backtesting
├── config.example.json # Configuration template
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Trading Strategy

The bot uses a combination of:

1. **RSI (Relative Strength Index)**: Identifies overbought/oversold conditions
2. **Moving Averages**: Trend confirmation
3. **Volume Analysis**: Confirms price movements
4. **Machine Learning**: Pattern recognition for enhanced signals

## Dashboard Features

- Real-time portfolio value
- Active trades
- Trading signals
- Price charts
- Performance metrics
- Historical trades

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please read CONTRIBUTING.md first.

## Support

For issues and questions, please open a GitHub issue.

---

**Remember**: Past performance does not guarantee future results. Always do your own research.