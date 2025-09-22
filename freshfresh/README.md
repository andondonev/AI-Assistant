# CRO/USDC Trading Bot for Cronos Network

An automated trading bot that monitors market signals and executes CRO/USDC trades on the Cronos network using VVS Finance DEX.

## Features

- 🤖 **Automated Trading**: Monitors market every minute for trading opportunities
- 📊 **Market Analysis**: Detects simultaneous up/down spikes across multiple exchanges
- 💱 **DEX Integration**: Executes trades on VVS Finance (Cronos network)
- 📱 **Telegram Interface**: Full control and monitoring via Telegram bot
- ⚙️ **Configurable**: Adjustable trade amounts, slippage, and risk parameters
- 🔒 **Secure**: Private key management and transaction signing
- 📈 **Real-time Monitoring**: Live status updates and trade notifications

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configuration

The bot is pre-configured with your wallet details:
- **Wallet Address**: 0x297c957d09A7bdFe3C5555b0cA8c06d6DbFC3440
- **Network**: Cronos (Chain ID: 25)
- **Trading Pair**: CRO/USDC

### 3. Run the Bot

```bash
python main.py
```

## Telegram Commands

Once the bot is running, you can control it via Telegram (@naandon_bot):

- `/start` - Welcome message and bot overview
- `/status` - Check bot status and recent activity
- `/balance` - View wallet balances (CRO, USDC)
- `/config` - Configure trading parameters
- `/trade` - Execute manual trades
- `/start_bot` - Start automated trading
- `/stop` - Stop automated trading

## Configuration Options

- **Trade Amount**: USDC amount per trade (default: $100)
- **Slippage**: Maximum slippage tolerance (default: 2%)
- **Min Price Change**: Minimum price change to trigger trade (default: 5%)
- **Max Daily Trades**: Maximum trades per day (default: 10)
- **Max Trade Amount**: Maximum USDC per trade (default: $1000)

## Trading Strategy

The bot uses a sophisticated market analysis approach:

1. **Signal Detection**: Monitors multiple exchanges (Binance, KuCoin, Crypto.com) for price spikes
2. **Spike Analysis**: Identifies simultaneous up/down movements across exchanges
3. **Trade Execution**: 
   - Simultaneous spikes → Buy CRO (volatility play)
   - Strong upward movement → Buy CRO
   - Strong downward movement → Sell CRO (if holding)

## Safety Features

- **Daily Trade Limits**: Prevents overtrading
- **Balance Checks**: Ensures sufficient funds before trading
- **Slippage Protection**: Configurable maximum slippage
- **Error Handling**: Comprehensive error logging and recovery
- **Manual Override**: Stop/start trading at any time

## Monitoring

The bot provides real-time monitoring through:
- Telegram notifications for all trades
- Detailed status reports
- Activity logs
- Balance tracking
- Performance metrics

## Files Structure

```
freshfresh/
├── main.py              # Main application entry point
├── trading_bot.py       # Core trading logic
├── telegram_bot.py      # Telegram interface
├── market_analyzer.py   # Market analysis and signal detection
├── dex_trader.py        # DEX trading operations
├── wallet_manager.py    # Wallet and transaction management
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Security Notes

- Your wallet recovery phrase is stored in the configuration
- The bot runs locally on your machine
- Private keys are never transmitted over the network
- All transactions are signed locally

## Support

For issues or questions:
1. Check the logs in `trading_bot.log`
2. Use `/status` command in Telegram
3. Monitor the console output for errors

## Disclaimer

This bot is for educational and personal use. Trading cryptocurrencies involves risk. Use at your own discretion and never invest more than you can afford to lose.
