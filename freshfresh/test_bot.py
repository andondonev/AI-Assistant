#!/usr/bin/env python3
"""
Test script for the CRO/USDC Trading Bot
"""

import sys
import time
from trading_bot import TradingBot
from market_analyzer import MarketAnalyzer
from wallet_manager import WalletManager

def test_wallet_connection():
    """Test wallet connection and balance retrieval"""
    print("🔍 Testing wallet connection...")
    try:
        wallet = WalletManager()
        print(f"✅ Wallet connected: {wallet.address}")
        
        # Test native CRO balance
        native_balance = wallet.get_balance()
        print(f"✅ Native CRO balance: {native_balance:.4f} CRO")
        
        return True
    except Exception as e:
        print(f"❌ Wallet connection failed: {str(e)}")
        return False

def test_market_analyzer():
    """Test market analysis functionality"""
    print("\n🔍 Testing market analyzer...")
    try:
        analyzer = MarketAnalyzer()
        
        # Test current price fetching
        print("Fetching current prices...")
        prices = analyzer.get_current_price('CRO/USDT')
        if prices:
            print(f"✅ Current CRO prices: {prices}")
        else:
            print("⚠️ No price data available")
        
        # Test signal analysis
        print("Analyzing market signals...")
        signal, message = analyzer.analyze_market_signal('CRO/USDT')
        if signal:
            print(f"✅ Signal detected: {signal['type']} - {message}")
        else:
            print(f"ℹ️ No signal: {message}")
        
        return True
    except Exception as e:
        print(f"❌ Market analyzer failed: {str(e)}")
        return False

def test_trading_bot():
    """Test trading bot functionality"""
    print("\n🔍 Testing trading bot...")
    try:
        bot = TradingBot()
        
        # Test status
        status = bot.get_status()
        print(f"✅ Bot status: {status}")
        
        # Test balance retrieval
        balances = bot.get_balances()
        print(f"✅ Balances: {balances}")
        
        # Test configuration
        print(f"✅ Configuration: {bot.config}")
        
        return True
    except Exception as e:
        print(f"❌ Trading bot failed: {str(e)}")
        return False

def test_manual_trade():
    """Test manual trade execution (dry run)"""
    print("\n🔍 Testing manual trade execution...")
    try:
        bot = TradingBot()
        
        # Test signal checking
        signal, message = bot.check_market_signal()
        print(f"✅ Market signal check: {message}")
        
        # Note: We won't execute actual trades in test mode
        print("ℹ️ Manual trade execution skipped (test mode)")
        
        return True
    except Exception as e:
        print(f"❌ Manual trade test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting CRO/USDC Trading Bot Tests\n")
    
    tests = [
        ("Wallet Connection", test_wallet_connection),
        ("Market Analyzer", test_market_analyzer),
        ("Trading Bot", test_trading_bot),
        ("Manual Trade", test_manual_trade)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
        
        time.sleep(1)  # Brief pause between tests
    
    print(f"\n{'='*50}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to run.")
        print("\nTo start the bot, run: python main.py")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("The bot may still work, but some features might be limited.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
