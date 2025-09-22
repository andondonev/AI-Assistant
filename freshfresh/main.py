#!/usr/bin/env python3
"""
CRO/USDC Trading Bot for Cronos Network
Automated trading bot that monitors market signals and executes trades
"""

import sys
import signal
import logging
from trading_bot import TradingBot
from telegram_bot import TelegramBotInterface

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received. Stopping bot...")
    if 'trading_bot' in globals():
        trading_bot.stop()
    if 'telegram_bot' in globals():
        telegram_bot.stop()
    sys.exit(0)

def main():
    """Main function"""
    logger.info("Starting CRO/USDC Trading Bot...")
    
    try:
        # Initialize trading bot
        global trading_bot
        trading_bot = TradingBot()
        
        # Initialize Telegram bot interface
        global telegram_bot
        telegram_bot = TelegramBotInterface(trading_bot)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the trading bot
        if trading_bot.start():
            logger.info("Trading bot started successfully")
        else:
            logger.error("Failed to start trading bot")
            return
        
        # Start the Telegram bot
        logger.info("Starting Telegram bot interface...")
        telegram_bot.run()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        if 'trading_bot' in globals():
            trading_bot.stop()
        logger.info("Trading bot stopped")

if __name__ == "__main__":
    main()
