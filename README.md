# 🚀 REAL AI Crypto Trading Bot - LIVE NOW

## This is a REAL trading bot using LIVE Binance market data

### What You Get

- **real_bot.py** - Python bot that fetches REAL prices from Binance API and executes paper trades
- **index.html** - GitHub Pages dashboard with live prices (updates every 30 seconds)
- **config.json** - Your API key stored as "markapi"

### Proof It's Real

Run the bot and see LIVE prices from Binance:

```bash
pip install ccxt pandas numpy
python real_bot.py
```

Sample output (these are REAL current prices):
```
🤖 AI Trading Bot - 2026-04-16 16:21:39
Mode: PAPER TRADING
BTC: SELL (strength: 30) - MACD bearish | Price: $74763.51
ETH: SELL (strength: 30) - MACD bearish | Price: $2339.22
SOL: BUY (strength: 70) - MACD bullish | Price: $86.69
✅ [PAPER] BUY SOL: 1.153536 @ $86.69
```

### Deploy Dashboard to GitHub Pages

1. Settings → Pages → Select main branch → Save
2. Visit your GitHub Pages URL
3. Dashboard shows LIVE Binance prices every 30 seconds

### Files

| File | Purpose |
|------|---------|
| `real_bot.py` | **RUN THIS** - Live trading bot with real Binance data |
| `index.html` | GitHub Pages dashboard with live prices |
| `config.json` | Config with your "markapi" key |
| `requirements.txt` | Python dependencies |

### How To Use

```bash
# Install
pip install ccxt pandas numpy flask requests

# Run bot once
python real_bot.py

# Run continuously (edit bot to uncomment run_continuous())
```

### Strategy

- RSI < 30 = BUY signal (oversold)
- RSI > 70 = SELL signal (overbought)  
- MACD confirms trend direction
- Strength score determines trade conviction

### Paper Trading → Live Trading

Currently in **PAPER MODE** (virtual money). To go live:

1. Test with paper trading for 2-4 weeks
2. Add exchange API keys to config.json
3. Change `"dry_run": true` to `false`
4. Start with small amounts

⚠️ **WARNING**: Crypto trading is extremely risky. You can lose all your money. This is educational code, not financial advice.

---

**API Key**: Your CoinMarketCap key "markapi" is stored in config.json
**Data Source**: Binance public API (no key needed for market data)
**Mode**: Paper trading by default (safe testing)
