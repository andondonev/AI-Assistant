#!/bin/bash

# CRO/USDC Trading Bot Startup Script

echo "🚀 Starting CRO/USDC Trading Bot..."
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python3 test_bot.py

if [ $? -eq 0 ]; then
    echo "✅ Tests passed! Starting bot..."
    echo ""
    echo "🤖 Bot is now running..."
    echo "📱 Use Telegram bot @naandon_bot to control the trading bot"
    echo "🛑 Press Ctrl+C to stop the bot"
    echo ""
    
    # Start the main bot
    python3 main.py
else
    echo "❌ Tests failed. Please check the errors above."
    exit 1
fi
