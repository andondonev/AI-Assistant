import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN, DEFAULT_TRADE_AMOUNT, DEFAULT_SLIPPAGE
from trading_bot import TradingBot

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBotInterface:
    def __init__(self, trading_bot):
        self.trading_bot = trading_bot
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("config", self.config_command))
        self.application.add_handler(CommandHandler("trade", self.trade_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        self.application.add_handler(CommandHandler("start_bot", self.start_bot_command))
        self.application.add_handler(CommandHandler("force_check", self.force_check_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="main_status"),
                InlineKeyboardButton("💰 Balance", callback_data="main_balance")
            ],
            [
                InlineKeyboardButton("⚙️ Configure", callback_data="main_config"),
                InlineKeyboardButton("💱 Trade", callback_data="main_trade")
            ],
            [
                InlineKeyboardButton("▶️ Start Bot", callback_data="main_start"),
                InlineKeyboardButton("⏹️ Stop Bot", callback_data="main_stop")
            ],
            [
                InlineKeyboardButton("🔄 Force Check", callback_data="main_force_check"),
                InlineKeyboardButton("📋 Commands List", callback_data="main_commands")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = f"""
🤖 CRO/USDC Trading Bot

Welcome! I'm your automated trading bot for the Cronos network.

Current Configuration:
• Trade Amount: ${DEFAULT_TRADE_AMOUNT} USDC
• Slippage: {DEFAULT_SLIPPAGE}%
• Signal Check: Every minute
• Wallet: 0x297c...3440

Use the buttons below to navigate, or type commands like /status, /balance, etc.
        """
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status = self.trading_bot.get_status()
        
        status_message = f"""
📊 Bot Status

Trading Status: {'🟢 Active' if status['is_running'] else '🔴 Stopped'}
Last Signal Check: {status['last_check']}
Total Trades Today: {status['trades_today']}
Successful Trades: {status['successful_trades']}
Failed Trades: {status['failed_trades']}

Recent Activity:
{status['recent_activity']}

Current Configuration:
• Trade Amount: ${status['trade_amount']} USDC
• Slippage: {status['slippage']}%
• Min Price Change: {status['min_price_change']}%
        """
        
        await update.message.reply_text(status_message)
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        try:
            balances = self.trading_bot.get_balances()
            
            balance_message = f"""
💰 Wallet Balances

Wrapped CRO (for trading): {balances['cro']:.4f} CRO
USDC Balance: {balances['usdc']:.2f} USDC
Native WCRO: {balances['wcro']:.4f} WCRO

Wallet Address: 0x297c...3440
Network: Cronos (Chain ID: 25)
            """
            
            await update.message.reply_text(balance_message)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching balances: {str(e)}")
    
    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /config command"""
        keyboard = [
            [
                InlineKeyboardButton("Trade Amount", callback_data="config_amount"),
                InlineKeyboardButton("Slippage", callback_data="config_slippage")
            ],
            [
                InlineKeyboardButton("Min Price Change", callback_data="config_min_change"),
                InlineKeyboardButton("Max Daily Trades", callback_data="config_max_trades")
            ],
            [
                InlineKeyboardButton("Set as Default", callback_data="config_set_default"),
                InlineKeyboardButton("Load Default", callback_data="config_load_default")
            ],
            [
                InlineKeyboardButton("View Current Config", callback_data="view_config")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚙️ **Configuration Menu**\n\nSelect a parameter to configure:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def trade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trade command"""
        keyboard = [
            [
                InlineKeyboardButton("Buy CRO", callback_data="trade_buy"),
                InlineKeyboardButton("Sell CRO", callback_data="trade_sell")
            ],
            [
                InlineKeyboardButton("Check Market Signal", callback_data="check_signal")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💱 **Manual Trading**\n\nSelect an action:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_bot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start_bot command"""
        try:
            if self.trading_bot.start():
                await update.message.reply_text("✅ **Trading bot started successfully!**\n\nThe bot will now monitor the market every minute for trading opportunities.", parse_mode='Markdown')
            else:
                await update.message.reply_text("⚠️ **Bot is already running!**")
        except Exception as e:
            await update.message.reply_text(f"❌ **Error starting bot:** {str(e)}", parse_mode='Markdown')
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        try:
            if self.trading_bot.stop():
                await update.message.reply_text("🛑 **Trading bot stopped successfully!**")
            else:
                await update.message.reply_text("⚠️ **Bot is already stopped!**")
        except Exception as e:
            await update.message.reply_text(f"❌ **Error stopping bot:** {str(e)}", parse_mode='Markdown')
    
    async def force_check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /force_check command"""
        try:
            status = self.trading_bot.force_signal_check()
            
            # Clean the recent activity text to avoid parsing errors
            recent_activity = status['recent_activity'].replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
            
            await update.message.reply_text(
                f"🔄 Forced Signal Check Completed\n\n"
                f"Last Check: {status['last_check']}\n"
                f"Recent Activity:\n{recent_activity}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error forcing signal check: {str(e)}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "config_amount":
            keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "💰 Configure Trade Amount\n\n"
                "Send a message with the new trade amount in USDC.\n"
                "Example: 100 for $100 USDC per trade\n\n"
                "Current amount: ${} USDC".format(self.trading_bot.config['trade_amount']),
                reply_markup=reply_markup
            )
            # Store the state for the next message
            context.user_data['waiting_for'] = 'amount'
            
        elif data == "config_slippage":
            keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📊 Configure Slippage\n\n"
                "Send a message with the new slippage percentage.\n"
                "Example: 2.5 for 2.5% slippage\n\n"
                "Current slippage: {}%".format(self.trading_bot.config['slippage']),
                reply_markup=reply_markup
            )
            context.user_data['waiting_for'] = 'slippage'
            
        elif data == "config_min_change":
            keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📈 Configure Minimum Price Change\n\n"
                "Send a message with the new minimum price change percentage.\n"
                "Example: 5.0 for 5% minimum change\n\n"
                "Current minimum: {}%".format(self.trading_bot.config['min_price_change']),
                reply_markup=reply_markup
            )
            context.user_data['waiting_for'] = 'min_change'
            
        elif data == "config_max_trades":
            keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔢 Configure Max Daily Trades\n\n"
                "Send a message with the new maximum daily trades.\n"
                "Example: 15 for 15 trades per day\n\n"
                "Current maximum: {} trades".format(self.trading_bot.config['max_daily_trades']),
                reply_markup=reply_markup
            )
            context.user_data['waiting_for'] = 'max_trades'
            
        elif data == "config_set_default":
            try:
                # Save current configuration as default
                self.trading_bot.save_as_default_config()
                keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                config = self.trading_bot.config
                config_message = f"""
✅ Configuration Saved as Default

Current settings have been saved as the new default configuration:

Trade Amount: ${config['trade_amount']} USDC
Slippage: {config['slippage']}%
Min Price Change: {config['min_price_change']}%
Max Daily Trades: {config['max_daily_trades']}
Signal Check Interval: {config['signal_check_interval']} seconds
Max Trade Amount: ${config['max_trade_amount']} USDC
Min Balance Threshold: ${config['min_balance_threshold']} USDC

These settings will be loaded when the bot starts or when you use "Load Default".
                """
                await query.edit_message_text(config_message, reply_markup=reply_markup)
            except Exception as e:
                keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"❌ Error saving default config: {str(e)}", reply_markup=reply_markup)
                
        elif data == "config_load_default":
            try:
                # Load default configuration
                self.trading_bot.load_default_config()
                keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                config = self.trading_bot.config
                config_message = f"""
✅ Default Configuration Loaded

Configuration has been reset to default values:

Trade Amount: ${config['trade_amount']} USDC
Slippage: {config['slippage']}%
Min Price Change: {config['min_price_change']}%
Max Daily Trades: {config['max_daily_trades']}
Signal Check Interval: {config['signal_check_interval']} seconds
Max Trade Amount: ${config['max_trade_amount']} USDC
Min Balance Threshold: ${config['min_balance_threshold']} USDC
                """
                await query.edit_message_text(config_message, reply_markup=reply_markup)
            except Exception as e:
                keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"❌ Error loading default config: {str(e)}", reply_markup=reply_markup)
            
        elif data == "view_config":
            keyboard = [[InlineKeyboardButton("🔙 Back to Config", callback_data="main_config")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            config = self.trading_bot.config
            is_default = self.trading_bot.is_current_config_default()
            default_status = " (Default)" if is_default else ""
            
            config_message = f"""
⚙️ Current Configuration{default_status}

Trade Amount: ${config['trade_amount']} USDC
Slippage: {config['slippage']}%
Min Price Change: {config['min_price_change']}%
Max Daily Trades: {config['max_daily_trades']}
Signal Check Interval: {config['signal_check_interval']} seconds
Max Trade Amount: ${config['max_trade_amount']} USDC
Min Balance Threshold: ${config['min_balance_threshold']} USDC
            """
            await query.edit_message_text(config_message, reply_markup=reply_markup)
            
        elif data == "trade_buy":
            try:
                result = self.trading_bot.execute_manual_trade('buy')
                keyboard = [[InlineKeyboardButton("🔙 Back to Trade Menu", callback_data="main_trade")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if result['success']:
                    await query.edit_message_text(
                        f"✅ Buy Order Executed\n\n"
                        f"Transaction Hash: {result['tx_hash']}\n"
                        f"Amount: ${result['amount_in']} USDC\n"
                        f"Expected CRO: {result['expected_amount_out']:.4f} CRO",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text(f"❌ Buy Order Failed\n\n{result['error']}", reply_markup=reply_markup)
            except Exception as e:
                keyboard = [[InlineKeyboardButton("🔙 Back to Trade Menu", callback_data="main_trade")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"❌ Error executing buy order: {str(e)}", reply_markup=reply_markup)
                
        elif data == "trade_sell":
            try:
                result = self.trading_bot.execute_manual_trade('sell')
                keyboard = [[InlineKeyboardButton("🔙 Back to Trade Menu", callback_data="main_trade")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if result['success']:
                    await query.edit_message_text(
                        f"✅ Sell Order Executed\n\n"
                        f"Transaction Hash: {result['tx_hash']}\n"
                        f"Amount: {result['amount_in']:.4f} CRO\n"
                        f"Expected USDC: ${result['expected_amount_out']:.2f} USDC",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text(f"❌ Sell Order Failed\n\n{result['error']}", reply_markup=reply_markup)
            except Exception as e:
                keyboard = [[InlineKeyboardButton("🔙 Back to Trade Menu", callback_data="main_trade")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"❌ Error executing sell order: {str(e)}", reply_markup=reply_markup)
                
        elif data == "check_signal":
            try:
                signal, message = self.trading_bot.check_market_signal()
                keyboard = [[InlineKeyboardButton("🔙 Back to Trade Menu", callback_data="main_trade")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if signal:
                    # Clean signal details to avoid parsing errors
                    signal_type = str(signal.get('type', 'Unknown')).replace('*', '').replace('_', '').replace('`', '')
                    signal_message = f"""
🔍 Market Signal Detected

Type: {signal_type}
Message: {str(message).replace('*', '').replace('_', '').replace('`', '')}
Timestamp: {signal.get('timestamp', 'Unknown')}
Exchanges: {', '.join(signal.get('exchanges', []))}

Details:
{self._format_signal_details(signal).replace('*', '').replace('_', '').replace('`', '')}
                    """
                    await query.edit_message_text(signal_message, reply_markup=reply_markup)
                else:
                    await query.edit_message_text(f"🔍 No Signal\n\n{message}", reply_markup=reply_markup)
            except Exception as e:
                keyboard = [[InlineKeyboardButton("🔙 Back to Trade Menu", callback_data="main_trade")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"❌ Error checking signal: {str(e)}", reply_markup=reply_markup)
        
        elif data == "trade_wrap":
            try:
                result = self.trading_bot.wrap_wcro_to_cro(1.0)  # Try to wrap 1 WCRO
                keyboard = [[InlineKeyboardButton("🔙 Back to Trade Menu", callback_data="main_trade")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if result['success']:
                    await query.edit_message_text(
                        f"✅ WCRO Wrapped Successfully\n\n"
                        f"Amount: 1.0 WCRO → 1.0 CRO",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text(
                        f"ℹ️ WCRO Wrapping Info\n\n{result['error']}\n\n"
                        f"To wrap your WCRO to CRO:\n"
                        f"1. Go to VVS Finance (vvs.finance)\n"
                        f"2. Connect your wallet\n"
                        f"3. Use the 'Wrap' function\n"
                        f"4. Wrap your WCRO to CRO tokens",
                        reply_markup=reply_markup
                    )
            except Exception as e:
                keyboard = [[InlineKeyboardButton("🔙 Back to Trade Menu", callback_data="main_trade")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"❌ Error wrapping WCRO: {str(e)}", reply_markup=reply_markup)
        
        # Main menu handlers
        elif data == "main_status":
            await self._show_status(query)
        elif data == "main_balance":
            await self._show_balance(query)
        elif data == "main_config":
            await self._show_config_menu(query)
        elif data == "main_trade":
            await self._show_trade_menu(query)
        elif data == "main_start":
            await self._start_bot_from_menu(query)
        elif data == "main_stop":
            await self._stop_bot_from_menu(query)
        elif data == "main_commands":
            await self._show_commands_list(query)
        elif data == "main_force_check":
            await self._force_check_from_menu(query)
        elif data == "back_to_main":
            await self._show_main_menu(query)
    
    def _format_signal_details(self, signal):
        """Format signal details for display"""
        if signal['type'] == 'simultaneous_spikes':
            return f"Up Spikes: {len(signal['up_spikes'])}\nDown Spikes: {len(signal['down_spikes'])}\nAvg Up: {signal['avg_up_magnitude']:.2f}%\nAvg Down: {signal['avg_down_magnitude']:.2f}%"
        elif signal['type'] in ['strong_upward', 'strong_downward']:
            return f"Spikes: {len(signal['spikes'])}\nAvg Magnitude: {signal['avg_magnitude']:.2f}%"
        return "No additional details"
    
    async def _show_main_menu(self, query):
        """Show main menu"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="main_status"),
                InlineKeyboardButton("💰 Balance", callback_data="main_balance")
            ],
            [
                InlineKeyboardButton("⚙️ Configure", callback_data="main_config"),
                InlineKeyboardButton("💱 Trade", callback_data="main_trade")
            ],
            [
                InlineKeyboardButton("▶️ Start Bot", callback_data="main_start"),
                InlineKeyboardButton("⏹️ Stop Bot", callback_data="main_stop")
            ],
            [
                InlineKeyboardButton("🔄 Force Check", callback_data="main_force_check"),
                InlineKeyboardButton("📋 Commands List", callback_data="main_commands")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"""
🤖 CRO/USDC Trading Bot

Current Configuration:
• Trade Amount: ${self.trading_bot.config['trade_amount']} USDC
• Slippage: {self.trading_bot.config['slippage']}%
• Signal Check: Every minute
• Wallet: 0x297c...3440

Use the buttons below to navigate, or type commands like /status, /balance, etc.
        """
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def _show_status(self, query):
        """Show status from menu"""
        status = self.trading_bot.get_status()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status_message = f"""
📊 Bot Status

Trading Status: {'🟢 Active' if status['is_running'] else '🔴 Stopped'}
Last Signal Check: {status['last_check']}
Total Trades Today: {status['trades_today']}
Successful Trades: {status['successful_trades']}
Failed Trades: {status['failed_trades']}

Recent Activity:
{status['recent_activity']}

Current Configuration:
• Trade Amount: ${status['trade_amount']} USDC
• Slippage: {status['slippage']}%
• Min Price Change: {status['min_price_change']}%
        """
        
        await query.edit_message_text(status_message, reply_markup=reply_markup)
    
    async def _show_balance(self, query):
        """Show balance from menu"""
        try:
            balances = self.trading_bot.get_balances()
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            balance_message = f"""
💰 Wallet Balances

Wrapped CRO (for trading): {balances['cro']:.4f} CRO
USDC Balance: {balances['usdc']:.2f} USDC
Native WCRO: {balances['wcro']:.4f} WCRO

Wallet Address: 0x297c...3440
Network: Cronos (Chain ID: 25)
            """
            
            await query.edit_message_text(balance_message, reply_markup=reply_markup)
            
        except Exception as e:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"❌ Error fetching balances: {str(e)}", reply_markup=reply_markup)
    
    async def _show_config_menu(self, query):
        """Show config menu from main menu"""
        keyboard = [
            [
                InlineKeyboardButton("Trade Amount", callback_data="config_amount"),
                InlineKeyboardButton("Slippage", callback_data="config_slippage")
            ],
            [
                InlineKeyboardButton("Min Price Change", callback_data="config_min_change"),
                InlineKeyboardButton("Max Daily Trades", callback_data="config_max_trades")
            ],
            [
                InlineKeyboardButton("Set as Default", callback_data="config_set_default"),
                InlineKeyboardButton("Load Default", callback_data="config_load_default")
            ],
            [
                InlineKeyboardButton("View Current Config", callback_data="view_config")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ Configuration Menu\n\nSelect a parameter to configure:",
            reply_markup=reply_markup
        )
    
    async def _show_trade_menu(self, query):
        """Show trade menu from main menu"""
        # Get current balances to show in the menu
        try:
            balances = self.trading_bot.get_balances()
            balance_info = f"\nCurrent Balances:\n• Wrapped CRO: {balances['cro']:.4f} CRO\n• USDC: {balances['usdc']:.2f} USDC\n• Native WCRO: {balances['wcro']:.4f} WCRO"
        except:
            balance_info = ""
        
        keyboard = [
            [
                InlineKeyboardButton("Buy CRO", callback_data="trade_buy"),
                InlineKeyboardButton("Sell CRO", callback_data="trade_sell")
            ],
            [
                InlineKeyboardButton("Wrap WCRO", callback_data="trade_wrap"),
                InlineKeyboardButton("Check Signal", callback_data="check_signal")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💱 Manual Trading{balance_info}\n\nSelect an action:",
            reply_markup=reply_markup
        )
    
    async def _start_bot_from_menu(self, query):
        """Start bot from main menu"""
        try:
            if self.trading_bot.start():
                keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "✅ Trading bot started successfully!\n\nThe bot will now monitor the market every minute for trading opportunities.",
                    reply_markup=reply_markup
                )
            else:
                keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("⚠️ Bot is already running!", reply_markup=reply_markup)
        except Exception as e:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"❌ Error starting bot: {str(e)}", reply_markup=reply_markup)
    
    async def _stop_bot_from_menu(self, query):
        """Stop bot from main menu"""
        try:
            if self.trading_bot.stop():
                keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("🛑 Trading bot stopped successfully!", reply_markup=reply_markup)
            else:
                keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("⚠️ Bot is already stopped!", reply_markup=reply_markup)
        except Exception as e:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"❌ Error stopping bot: {str(e)}", reply_markup=reply_markup)
    
    async def _show_commands_list(self, query):
        """Show commands list from main menu"""
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        commands_message = """
📋 Available Commands

/start - Show main menu
/status - Check bot status and recent activity
/balance - Check wallet balances
/config - Configure trading parameters
/trade - Execute manual trades
/start_bot - Start automated trading
/stop - Stop automated trading
/force_check - Force immediate signal check

You can also use the buttons in the main menu for easier navigation!
        """
        
        await query.edit_message_text(commands_message, reply_markup=reply_markup)
    
    async def _force_check_from_menu(self, query):
        """Force check from main menu"""
        try:
            status = self.trading_bot.force_signal_check()
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Clean the recent activity text to avoid parsing errors
            recent_activity = status['recent_activity'].replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
            
            await query.edit_message_text(
                f"🔄 Forced Signal Check Completed\n\n"
                f"Last Check: {status['last_check']}\n"
                f"Recent Activity:\n{recent_activity}",
                reply_markup=reply_markup
            )
        except Exception as e:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"❌ Error forcing signal check: {str(e)}", reply_markup=reply_markup)
    
    async def handle_config_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle configuration messages"""
        if 'waiting_for' not in context.user_data:
            return
        
        waiting_for = context.user_data['waiting_for']
        text = update.message.text
        
        try:
            if waiting_for == 'amount':
                amount = float(text)
                if amount > 0 and amount <= 1000:
                    self.trading_bot.update_config('trade_amount', amount)
                    await update.message.reply_text(f"✅ Trade amount updated to ${amount} USDC")
                else:
                    await update.message.reply_text("❌ Amount must be between $1 and $1000")
                    
            elif waiting_for == 'slippage':
                slippage = float(text)
                if 0.1 <= slippage <= 10:
                    self.trading_bot.update_config('slippage', slippage)
                    await update.message.reply_text(f"✅ Slippage updated to {slippage}%")
                else:
                    await update.message.reply_text("❌ Slippage must be between 0.1% and 10%")
                    
            elif waiting_for == 'min_change':
                min_change = float(text)
                if 1 <= min_change <= 50:
                    self.trading_bot.update_config('min_price_change', min_change)
                    await update.message.reply_text(f"✅ Minimum price change updated to {min_change}%")
                else:
                    await update.message.reply_text("❌ Minimum price change must be between 1% and 50%")
                    
            elif waiting_for == 'max_trades':
                max_trades = int(text)
                if 1 <= max_trades <= 100:
                    self.trading_bot.update_config('max_daily_trades', max_trades)
                    await update.message.reply_text(f"✅ Max daily trades updated to {max_trades}")
                else:
                    await update.message.reply_text("❌ Max daily trades must be between 1 and 100")
            
            # Clear the waiting state
            del context.user_data['waiting_for']
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number")
        except Exception as e:
            await update.message.reply_text(f"❌ Error updating configuration: {str(e)}")
    
    def run(self):
        """Start the Telegram bot"""
        # Add message handler for configuration
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_config_message))
        
        logger.info("Starting Telegram bot...")
        self.application.run_polling()

