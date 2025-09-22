#!/usr/bin/env python3
"""
Quick status check for the trading bot
"""

import sys
import time
from trading_bot import TradingBot

def check_bot_status():
    """Check if the bot is working properly"""
    try:
        print("🔍 Checking trading bot status...")
        
        # Create a new instance to check status
        bot = TradingBot()
        
        # Get status
        status = bot.get_status()
        print(f"✅ Bot Status: {'Running' if status['is_running'] else 'Stopped'}")
        print(f"✅ Last Check: {status['last_check']}")
        print(f"✅ Trades Today: {status['trades_today']}")
        print(f"✅ Successful Trades: {status['successful_trades']}")
        print(f"✅ Failed Trades: {status['failed_trades']}")
        
        # Get balances
        balances = bot.get_balances()
        print(f"✅ Wrapped CRO (for trading): {balances['cro']:.4f} CRO")
        print(f"✅ USDC Balance: {balances['usdc']:.4f} USDC")
        print(f"✅ Native WCRO: {balances['wcro']:.4f} WCRO")
        
        # Test market signal
        signal, message = bot.check_market_signal()
        print(f"✅ Market Signal: {message}")
        
        print("\n🎉 Bot is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking bot status: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_bot_status()
    sys.exit(0 if success else 1)
