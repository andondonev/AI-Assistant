import logging
import discord
from discord.ext import commands
from discord import app_commands
from config import DISCORD_BOT_TOKEN, DEFAULT_TRADE_AMOUNT, DEFAULT_SLIPPAGE
from trading_bot import TradingBot

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DiscordBotInterface:
    def __init__(self, trading_bot):
        self.trading_bot = trading_bot
        # Use only basic intents to avoid privileged intents requirement
        intents = discord.Intents.default()
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.setup_commands()
    
    def setup_commands(self):
        """Set up Discord slash commands"""
        
        @self.bot.event
        async def on_ready():
            logger.info(f'Discord bot logged in as {self.bot.user}')
            try:
                synced = await self.bot.tree.sync()
                logger.info(f'Synced {len(synced)} command(s)')
            except Exception as e:
                logger.error(f'Failed to sync commands: {e}')
        
        @self.bot.tree.command(name="start", description="Show the main trading bot menu")
        async def start_command(interaction: discord.Interaction):
            """Handle /start command"""
            # Create main menu embed
            price_info = self.trading_bot.get_price_info()
            bot_status = self.trading_bot.get_status()
            
            embed = discord.Embed(
                title="🤖 CRO/USDC Trading Bot",
                description="Welcome! I'm your automated trading bot for the Cronos network.",
                color=0x00ff00 if bot_status['is_running'] else 0xff0000
            )
            
            # Live status indicator
            if bot_status['is_running']:
                embed.add_field(
                    name="🟢 LIVE STATUS",
                    value=f"• Bot Status: Active & Monitoring\n• Trades Today: {bot_status['trades_today']}\n• Last Check: {bot_status['last_check']}\n• Signal Check: Every 60s",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔴 BOT STATUS",
                    value="• Bot Status: Stopped\n• Click 'Start Bot' to begin monitoring\n• Signal Check: Paused",
                    inline=False
                )
            
            # Price information
            embed.add_field(
                name="📈 Price Information",
                value=f"{price_info['price_summary']}\n{price_info['simple_chart']}\nMarket Pulse: {price_info['market_pulse']}",
                inline=False
            )
            
            # Current configuration
            embed.add_field(
                name="Current Configuration",
                value=f"• Trade Amount: ${self.trading_bot.config['trade_amount']} USDC\n• Slippage: {self.trading_bot.config['slippage']}%\n• Signal Check: Every minute\n• Wallet: 0x297c...3440",
                inline=False
            )
            
            embed.set_footer(text="Use the buttons below to navigate, or type commands like /status, /balance, etc.")
            
            view = MainMenuView(self.trading_bot)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        @self.bot.tree.command(name="status", description="Check bot status and recent activity")
        async def status_command(interaction: discord.Interaction):
            """Handle /status command"""
            status = self.trading_bot.get_status()
            
            embed = discord.Embed(
                title="📊 Bot Status",
                color=0x00ff00 if status['is_running'] else 0xff0000
            )
            
            embed.add_field(
                name="Trading Status",
                value="🟢 Active" if status['is_running'] else "🔴 Stopped",
                inline=True
            )
            embed.add_field(
                name="Last Signal Check",
                value=status['last_check'],
                inline=True
            )
            embed.add_field(
                name="Total Trades Today",
                value=str(status['trades_today']),
                inline=True
            )
            embed.add_field(
                name="Successful Trades",
                value=str(status['successful_trades']),
                inline=True
            )
            embed.add_field(
                name="Failed Trades",
                value=str(status['failed_trades']),
                inline=True
            )
            embed.add_field(
                name="Recent Activity",
                value=status['recent_activity'],
                inline=False
            )
            embed.add_field(
                name="Current Configuration",
                value=f"• Trade Amount: ${status['trade_amount']} USDC\n• Slippage: {status['slippage']}%\n• Min Price Change: {status['min_price_change']}%",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        @self.bot.tree.command(name="balance", description="Check wallet balances")
        async def balance_command(interaction: discord.Interaction):
            """Handle /balance command"""
            try:
                balances = self.trading_bot.get_balances()
                
                embed = discord.Embed(
                    title="💰 Wallet Balances",
                    color=0x0099ff
                )
                
                embed.add_field(
                    name="Wrapped CRO (for trading)",
                    value=f"{balances['cro']:.4f} CRO",
                    inline=True
                )
                embed.add_field(
                    name="USDC Balance",
                    value=f"{balances['usdc']:.2f} USDC",
                    inline=True
                )
                embed.add_field(
                    name="Native WCRO",
                    value=f"{balances['wcro']:.4f} WCRO",
                    inline=True
                )
                embed.add_field(
                    name="Wallet Address",
                    value="0x297c...3440",
                    inline=False
                )
                embed.add_field(
                    name="Network",
                    value="Cronos (Chain ID: 25)",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Error fetching balances: {str(e)}", ephemeral=True)
        
        @self.bot.tree.command(name="config", description="Configure trading parameters")
        async def config_command(interaction: discord.Interaction):
            """Handle /config command"""
            config = self.trading_bot.config
            
            embed = discord.Embed(
                title="⚙️ Configuration Menu",
                description="Select a parameter to configure:",
                color=0xff9900
            )
            
            embed.add_field(
                name="Current Settings",
                value=f"• Trade Amount: ${config['trade_amount']} USDC\n• Slippage: {config['slippage']}%\n• Min Price Change: {config['min_price_change']}%\n• Max Daily Trades: {config['max_daily_trades']}",
                inline=False
            )
            
            view = ConfigMenuView(self.trading_bot)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        @self.bot.tree.command(name="trade", description="Execute manual trades")
        async def trade_command(interaction: discord.Interaction):
            """Handle /trade command"""
            try:
                balances = self.trading_bot.get_balances()
                balance_info = f"• Wrapped CRO: {balances['cro']:.4f} CRO\n• USDC: {balances['usdc']:.2f} USDC\n• Native WCRO: {balances['wcro']:.4f} WCRO"
            except:
                balance_info = "Unable to fetch balances"
            
            embed = discord.Embed(
                title="💱 Manual Trading",
                description=f"Current Balances:\n{balance_info}\n\nSelect an action:",
                color=0x00ff99
            )
            
            view = TradeMenuView(self.trading_bot)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        @self.bot.tree.command(name="start_bot", description="Start automated trading")
        async def start_bot_command(interaction: discord.Interaction):
            """Handle /start_bot command"""
            try:
                if self.trading_bot.start():
                    await interaction.response.send_message("✅ **Trading bot started successfully!**\n\nThe bot will now monitor the market every minute for trading opportunities.", ephemeral=True)
                else:
                    await interaction.response.send_message("⚠️ **Bot is already running!**", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ **Error starting bot:** {str(e)}", ephemeral=True)
        
        @self.bot.tree.command(name="stop", description="Stop automated trading")
        async def stop_command(interaction: discord.Interaction):
            """Handle /stop command"""
            try:
                if self.trading_bot.stop():
                    await interaction.response.send_message("🛑 **Trading bot stopped successfully!**", ephemeral=True)
                else:
                    await interaction.response.send_message("⚠️ **Bot is already stopped!**", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ **Error stopping bot:** {str(e)}", ephemeral=True)
        
        @self.bot.tree.command(name="force_check", description="Force immediate signal check")
        async def force_check_command(interaction: discord.Interaction):
            """Handle /force_check command"""
            try:
                status = self.trading_bot.force_signal_check()
                recent_activity = status['recent_activity'].replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
                
                embed = discord.Embed(
                    title="�� Forced Signal Check Completed",
                    color=0x00ff00
                )
                embed.add_field(name="Last Check", value=status['last_check'], inline=False)
                embed.add_field(name="Recent Activity", value=recent_activity, inline=False)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Error forcing signal check: {str(e)}", ephemeral=True)
    
    async def _create_main_embed(self):
        """Create main menu embed"""
        price_info = self.trading_bot.get_price_info()
        bot_status = self.trading_bot.get_status()
        
        embed = discord.Embed(
            title="�� CRO/USDC Trading Bot",
            description="Welcome! I'm your automated trading bot for the Cronos network.",
            color=0x00ff00 if bot_status['is_running'] else 0xff0000
        )
        
        # Live status indicator
        if bot_status['is_running']:
            embed.add_field(
                name="�� LIVE STATUS",
                value=f"• Bot Status: Active & Monitoring\n• Trades Today: {bot_status['trades_today']}\n• Last Check: {bot_status['last_check']}\n• Signal Check: Every 60s",
                inline=False
            )
        else:
            embed.add_field(
                name="�� BOT STATUS",
                value="• Bot Status: Stopped\n• Click 'Start Bot' to begin monitoring\n• Signal Check: Paused",
                inline=False
            )
        
        # Price information
        embed.add_field(
            name="📈 Price Information",
            value=f"{price_info['price_summary']}\n{price_info['simple_chart']}\nMarket Pulse: {price_info['market_pulse']}",
            inline=False
        )
        
        # Current configuration
        embed.add_field(
            name="Current Configuration",
            value=f"• Trade Amount: ${self.trading_bot.config['trade_amount']} USDC\n• Slippage: {self.trading_bot.config['slippage']}%\n• Signal Check: Every minute\n• Wallet: 0x297c...3440",
            inline=False
        )
        
        embed.set_footer(text="Use the buttons below to navigate, or type commands like /status, /balance, etc.")
        return embed
    
    async def _create_status_embed(self):
        """Create status embed"""
        status = self.trading_bot.get_status()
        
        embed = discord.Embed(
            title="📊 Bot Status",
            color=0x00ff00 if status['is_running'] else 0xff0000
        )
        
        embed.add_field(
            name="Trading Status",
            value="🟢 Active" if status['is_running'] else "🔴 Stopped",
            inline=True
        )
        embed.add_field(
            name="Last Signal Check",
            value=status['last_check'],
            inline=True
        )
        embed.add_field(
            name="Total Trades Today",
            value=str(status['trades_today']),
            inline=True
        )
        embed.add_field(
            name="Successful Trades",
            value=str(status['successful_trades']),
            inline=True
        )
        embed.add_field(
            name="Failed Trades",
            value=str(status['failed_trades']),
            inline=True
        )
        embed.add_field(
            name="Recent Activity",
            value=status['recent_activity'],
            inline=False
        )
        embed.add_field(
            name="Current Configuration",
            value=f"• Trade Amount: ${status['trade_amount']} USDC\n• Slippage: {status['slippage']}%\n• Min Price Change: {status['min_price_change']}%",
            inline=False
        )
        
        return embed
    
    async def _create_balance_embed(self):
        """Create balance embed"""
        balances = self.trading_bot.get_balances()
        
        embed = discord.Embed(
            title="💰 Wallet Balances",
            color=0x0099ff
        )
        
        embed.add_field(
            name="Wrapped CRO (for trading)",
            value=f"{balances['cro']:.4f} CRO",
            inline=True
        )
        embed.add_field(
            name="USDC Balance",
            value=f"{balances['usdc']:.2f} USDC",
            inline=True
        )
        embed.add_field(
            name="Native WCRO",
            value=f"{balances['wcro']:.4f} WCRO",
            inline=True
        )
        embed.add_field(
            name="Wallet Address",
            value="0x297c...3440",
            inline=False
        )
        embed.add_field(
            name="Network",
            value="Cronos (Chain ID: 25)",
            inline=False
        )
        
        return embed
    
    async def _create_config_embed(self):
        """Create config embed"""
        config = self.trading_bot.config
        
        embed = discord.Embed(
            title="⚙️ Configuration Menu",
            description="Select a parameter to configure:",
            color=0xff9900
        )
        
        embed.add_field(
            name="Current Settings",
            value=f"• Trade Amount: ${config['trade_amount']} USDC\n• Slippage: {config['slippage']}%\n• Min Price Change: {config['min_price_change']}%\n• Max Daily Trades: {config['max_daily_trades']}",
            inline=False
        )
        
        return embed
    
    async def _create_trade_embed(self):
        """Create trade embed"""
        try:
            balances = self.trading_bot.get_balances()
            balance_info = f"• Wrapped CRO: {balances['cro']:.4f} CRO\n• USDC: {balances['usdc']:.2f} USDC\n• Native WCRO: {balances['wcro']:.4f} WCRO"
        except:
            balance_info = "Unable to fetch balances"
        
        embed = discord.Embed(
            title="💱 Manual Trading",
            description=f"Current Balances:\n{balance_info}\n\nSelect an action:",
            color=0x00ff99
        )
        
        return embed
    
    def run(self):
        """Start the Discord bot"""
        logger.info("Starting Discord bot...")
        self.bot.run(DISCORD_BOT_TOKEN)

# Discord View Classes for Interactive Buttons
class MainMenuView(discord.ui.View):
    def __init__(self, trading_bot):
        super().__init__(timeout=None)
        self.trading_bot = trading_bot
    
    @discord.ui.button(label="📊 Status", style=discord.ButtonStyle.primary)
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self._create_status_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="💰 Balance", style=discord.ButtonStyle.primary)
    async def balance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = await self._create_balance_embed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching balances: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="⚙️ Configure", style=discord.ButtonStyle.secondary)
    async def config_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self._create_config_embed()
        view = ConfigMenuView(self.trading_bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="💱 Trade", style=discord.ButtonStyle.secondary)
    async def trade_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self._create_trade_embed()
        view = TradeMenuView(self.trading_bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="▶️ Start Bot", style=discord.ButtonStyle.success)
    async def start_bot_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.trading_bot.start():
                await interaction.response.send_message("✅ **Trading bot started successfully!**\n\nThe bot will now monitor the market every minute for trading opportunities.", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ **Bot is already running!**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ **Error starting bot:** {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="⏹️ Stop Bot", style=discord.ButtonStyle.danger)
    async def stop_bot_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.trading_bot.stop():
                await interaction.response.send_message("🛑 **Trading bot stopped successfully!**", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ **Bot is already stopped!**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ **Error stopping bot:** {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="�� Force Check", style=discord.ButtonStyle.secondary)
    async def force_check_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            status = self.trading_bot.force_signal_check()
            recent_activity = status['recent_activity'].replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
            
            embed = discord.Embed(
                title="�� Forced Signal Check Completed",
                color=0x00ff00
            )
            embed.add_field(name="Last Check", value=status['last_check'], inline=False)
            embed.add_field(name="Recent Activity", value=recent_activity, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error forcing signal check: {str(e)}", ephemeral=True)
    
    async def _create_status_embed(self):
        """Create status embed"""
        status = self.trading_bot.get_status()
        
        embed = discord.Embed(
            title="📊 Bot Status",
            color=0x00ff00 if status['is_running'] else 0xff0000
        )
        
        embed.add_field(
            name="Trading Status",
            value="🟢 Active" if status['is_running'] else "🔴 Stopped",
            inline=True
        )
        embed.add_field(
            name="Last Signal Check",
            value=status['last_check'],
            inline=True
        )
        embed.add_field(
            name="Total Trades Today",
            value=str(status['trades_today']),
            inline=True
        )
        embed.add_field(
            name="Successful Trades",
            value=str(status['successful_trades']),
            inline=True
        )
        embed.add_field(
            name="Failed Trades",
            value=str(status['failed_trades']),
            inline=True
        )
        embed.add_field(
            name="Recent Activity",
            value=status['recent_activity'],
            inline=False
        )
        embed.add_field(
            name="Current Configuration",
            value=f"• Trade Amount: ${status['trade_amount']} USDC\n• Slippage: {status['slippage']}%\n• Min Price Change: {status['min_price_change']}%",
            inline=False
        )
        
        return embed
    
    async def _create_balance_embed(self):
        """Create balance embed"""
        balances = self.trading_bot.get_balances()
        
        embed = discord.Embed(
            title="💰 Wallet Balances",
            color=0x0099ff
        )
        
        embed.add_field(
            name="Wrapped CRO (for trading)",
            value=f"{balances['cro']:.4f} CRO",
            inline=True
        )
        embed.add_field(
            name="USDC Balance",
            value=f"{balances['usdc']:.2f} USDC",
            inline=True
        )
        embed.add_field(
            name="Native WCRO",
            value=f"{balances['wcro']:.4f} WCRO",
            inline=True
        )
        embed.add_field(
            name="Wallet Address",
            value="0x297c...3440",
            inline=False
        )
        embed.add_field(
            name="Network",
            value="Cronos (Chain ID: 25)",
            inline=False
        )
        
        return embed
    
    async def _create_config_embed(self):
        """Create config embed"""
        config = self.trading_bot.config
        
        embed = discord.Embed(
            title="⚙️ Configuration Menu",
            description="Select a parameter to configure:",
            color=0xff9900
        )
        
        embed.add_field(
            name="Current Settings",
            value=f"• Trade Amount: ${config['trade_amount']} USDC\n• Slippage: {config['slippage']}%\n• Min Price Change: {config['min_price_change']}%\n• Max Daily Trades: {config['max_daily_trades']}",
            inline=False
        )
        
        return embed
    
    async def _create_trade_embed(self):
        """Create trade embed"""
        try:
            balances = self.trading_bot.get_balances()
            balance_info = f"• Wrapped CRO: {balances['cro']:.4f} CRO\n• USDC: {balances['usdc']:.2f} USDC\n• Native WCRO: {balances['wcro']:.4f} WCRO"
        except:
            balance_info = "Unable to fetch balances"
        
        embed = discord.Embed(
            title="💱 Manual Trading",
            description=f"Current Balances:\n{balance_info}\n\nSelect an action:",
            color=0x00ff99
        )
        
        return embed

class ConfigMenuView(discord.ui.View):
    def __init__(self, trading_bot):
        super().__init__(timeout=None)
        self.trading_bot = trading_bot
    
    @discord.ui.button(label="Trade Amount", style=discord.ButtonStyle.primary)
    async def trade_amount_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ConfigModal("Trade Amount", "amount", self.trading_bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Slippage", style=discord.ButtonStyle.primary)
    async def slippage_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ConfigModal("Slippage", "slippage", self.trading_bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Min Price Change", style=discord.ButtonStyle.primary)
    async def min_change_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ConfigModal("Min Price Change", "min_change", self.trading_bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Max Daily Trades", style=discord.ButtonStyle.primary)
    async def max_trades_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ConfigModal("Max Daily Trades", "max_trades", self.trading_bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Set as Default", style=discord.ButtonStyle.success)
    async def set_default_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.trading_bot.save_as_default_config()
            config = self.trading_bot.config
            
            embed = discord.Embed(
                title="✅ Configuration Saved as Default",
                description="Current settings have been saved as the new default configuration:",
                color=0x00ff00
            )
            embed.add_field(
                name="Settings",
                value=f"• Trade Amount: ${config['trade_amount']} USDC\n• Slippage: {config['slippage']}%\n• Min Price Change: {config['min_price_change']}%\n• Max Daily Trades: {config['max_daily_trades']}\n• Signal Check Interval: {config['signal_check_interval']} seconds\n• Max Trade Amount: ${config['max_trade_amount']} USDC\n• Min Balance Threshold: ${config['min_balance_threshold']} USDC",
                inline=False
            )
            embed.add_field(
                name="Note",
                value="These settings will be loaded when the bot starts or when you use 'Load Default'.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error saving default config: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Load Default", style=discord.ButtonStyle.secondary)
    async def load_default_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.trading_bot.load_default_config()
            config = self.trading_bot.config
            
            embed = discord.Embed(
                title="✅ Default Configuration Loaded",
                description="Configuration has been reset to default values:",
                color=0x00ff00
            )
            embed.add_field(
                name="Settings",
                value=f"• Trade Amount: ${config['trade_amount']} USDC\n• Slippage: {config['slippage']}%\n• Min Price Change: {config['min_price_change']}%\n• Max Daily Trades: {config['max_daily_trades']}\n• Signal Check Interval: {config['signal_check_interval']} seconds\n• Max Trade Amount: ${config['max_trade_amount']} USDC\n• Min Balance Threshold: ${config['min_balance_threshold']} USDC",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error loading default config: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="View Current Config", style=discord.ButtonStyle.secondary)
    async def view_config_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.trading_bot.config
        is_default = self.trading_bot.is_current_config_default()
        default_status = " (Default)" if is_default else ""
        
        embed = discord.Embed(
            title=f"⚙️ Current Configuration{default_status}",
            color=0xff9900
        )
        embed.add_field(
            name="Settings",
            value=f"• Trade Amount: ${config['trade_amount']} USDC\n• Slippage: {config['slippage']}%\n• Min Price Change: {config['min_price_change']}%\n• Max Daily Trades: {config['max_daily_trades']}\n• Signal Check Interval: {config['signal_check_interval']} seconds\n• Max Trade Amount: ${config['max_trade_amount']} USDC\n• Min Balance Threshold: ${config['min_balance_threshold']} USDC",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TradeMenuView(discord.ui.View):
    def __init__(self, trading_bot):
        super().__init__(timeout=None)
        self.trading_bot = trading_bot
    
    @discord.ui.button(label="Buy CRO", style=discord.ButtonStyle.success)
    async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            result = self.trading_bot.execute_manual_trade('buy')
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Buy Order Executed",
                    color=0x00ff00
                )
                embed.add_field(name="Transaction Hash", value=result['tx_hash'], inline=False)
                embed.add_field(name="Amount", value=f"${result['amount_in']} USDC", inline=True)
                embed.add_field(name="Expected CRO", value=f"{result['expected_amount_out']:.4f} CRO", inline=True)
            else:
                embed = discord.Embed(
                    title="❌ Buy Order Failed",
                    description=result['error'],
                    color=0xff0000
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error executing buy order: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Sell CRO", style=discord.ButtonStyle.danger)
    async def sell_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            result = self.trading_bot.execute_manual_trade('sell')
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Sell Order Executed",
                    color=0x00ff00
                )
                embed.add_field(name="Transaction Hash", value=result['tx_hash'], inline=False)
                embed.add_field(name="Amount", value=f"{result['amount_in']:.4f} CRO", inline=True)
                embed.add_field(name="Expected USDC", value=f"${result['expected_amount_out']:.2f} USDC", inline=True)
            else:
                embed = discord.Embed(
                    title="❌ Sell Order Failed",
                    description=result['error'],
                    color=0xff0000
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error executing sell order: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Check Signal", style=discord.ButtonStyle.secondary)
    async def check_signal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            signal, message = self.trading_bot.check_market_signal()
            
            if signal:
                embed = discord.Embed(
                    title="�� Market Signal Detected",
                    color=0xffaa00
                )
                embed.add_field(name="Type", value=signal.get('type', 'Unknown'), inline=True)
                embed.add_field(name="Message", value=str(message).replace('*', '').replace('_', '').replace('`', ''), inline=False)
                embed.add_field(name="Timestamp", value=signal.get('timestamp', 'Unknown'), inline=True)
                embed.add_field(name="Exchanges", value=', '.join(signal.get('exchanges', [])), inline=True)
                
                if 'avg_magnitude' in signal:
                    embed.add_field(name="Average Magnitude", value=f"{signal['avg_magnitude']:.2f}%", inline=True)
            else:
                embed = discord.Embed(
                    title="🔍 No Signal",
                    description=message,
                    color=0x666666
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error checking signal: {str(e)}", ephemeral=True)

class ConfigModal(discord.ui.Modal):
    def __init__(self, title, config_type, trading_bot):
        super().__init__(title=f"Configure {title}")
        self.config_type = config_type
        self.trading_bot = trading_bot
        
        self.value_input = discord.ui.TextInput(
            label=f"New {title}",
            placeholder=f"Enter new {title.lower()}...",
            required=True
        )
        self.add_item(self.value_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = self.value_input.value
            
            if self.config_type == 'amount':
                amount = float(value)
                if amount > 0 and amount <= 1000:
                    self.trading_bot.update_config('trade_amount', amount)
                    await interaction.response.send_message(f"✅ Trade amount updated to ${amount} USDC", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Amount must be between $1 and $1000", ephemeral=True)
                    
            elif self.config_type == 'slippage':
                slippage = float(value)
                if 0.1 <= slippage <= 10:
                    self.trading_bot.update_config('slippage', slippage)
                    await interaction.response.send_message(f"✅ Slippage updated to {slippage}%", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Slippage must be between 0.1% and 10%", ephemeral=True)
                    
            elif self.config_type == 'min_change':
                min_change = float(value)
                if 1 <= min_change <= 50:
                    self.trading_bot.update_config('min_price_change', min_change)
                    await interaction.response.send_message(f"✅ Minimum price change updated to {min_change}%", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Minimum price change must be between 1% and 50%", ephemeral=True)
                    
            elif self.config_type == 'max_trades':
                max_trades = int(value)
                if 1 <= max_trades <= 100:
                    self.trading_bot.update_config('max_daily_trades', max_trades)
                    await interaction.response.send_message(f"✅ Max daily trades updated to {max_trades}", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Max daily trades must be between 1 and 100", ephemeral=True)
                    
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating configuration: {str(e)}", ephemeral=True)
