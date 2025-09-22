import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8252928580:AAGa8XgJNrnYuZwZnBBxUCdBr5DYZdBiHRc"
TELEGRAM_BOT_ID = 494929144

# Wallet Configuration
WALLET_ADDRESS = "0x297c957d09A7bdFe3C5555b0cA8c06d6DbFC3440"
RECOVERY_PHRASE = "grab gym giant atom turtle cost word analyst question nasty critic exercise"

# Cronos Network Configuration
CRONOS_RPC_URL = "https://evm.cronos.org"
CRONOS_CHAIN_ID = 25

# Token Addresses on Cronos
CRO_TOKEN_ADDRESS = "0x5C7F8A570d578ED84E63fdFA7b1eE72dEae1AE23"  # Wrapped CRO
USDC_TOKEN_ADDRESS = "0xc21223249CA28397B4B6541dfFaEcC539BfF0c59"  # USDC on Cronos

# DEX Configuration (VVS Finance on Cronos)
VVS_ROUTER_ADDRESS = "0x145863Eb42Cf62847A6Ca784e6416C1682b1b2Ae"
VVS_FACTORY_ADDRESS = "0x3B44B2a1876c0C4b0b63a048d6f4Fc1b0954d6f5"

# Trading Configuration
DEFAULT_TRADE_AMOUNT = 100  # USDC
DEFAULT_SLIPPAGE = 2.0  # 2%
MIN_PRICE_CHANGE = 2.0  # 2% minimum price change to trigger trade (more aggressive)
SIGNAL_CHECK_INTERVAL = 60  # seconds

# Market Analysis Configuration
PRICE_LOOKBACK_PERIODS = 3  # Number of periods to look back for spike detection (shorter lookback)
SPIKE_THRESHOLD = 1.5  # Percentage change to consider as spike (more sensitive)

# Safety Configuration
MAX_DAILY_TRADES = 10
MAX_TRADE_AMOUNT = 1000  # Maximum USDC per trade
MIN_BALANCE_THRESHOLD = 50  # Minimum USDC balance to maintain
