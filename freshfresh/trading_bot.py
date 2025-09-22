import time
import schedule
import threading
import json
import os
from datetime import datetime, timedelta
from wallet_manager import WalletManager
from market_analyzer import MarketAnalyzer
from dex_trader import DEXTrader
from config import (
    DEFAULT_TRADE_AMOUNT, DEFAULT_SLIPPAGE, MIN_PRICE_CHANGE,
    MAX_DAILY_TRADES, MAX_TRADE_AMOUNT, MIN_BALANCE_THRESHOLD,
    SIGNAL_CHECK_INTERVAL
)

class TradingBot:
    def __init__(self):
        self.wallet = WalletManager()
        self.market_analyzer = MarketAnalyzer()
        self.dex_trader = DEXTrader(self.wallet)
        
        # Bot state
        self.is_running = False
        self.trades_today = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.last_check = None
        self.recent_activity = []
        
        # Default configuration file path
        self.default_config_file = 'default_config.json'
        
        # Configuration
        self.config = {
            'trade_amount': DEFAULT_TRADE_AMOUNT,
            'slippage': DEFAULT_SLIPPAGE,
            'min_price_change': MIN_PRICE_CHANGE,
            'max_daily_trades': MAX_DAILY_TRADES,
            'max_trade_amount': MAX_TRADE_AMOUNT,
            'min_balance_threshold': MIN_BALANCE_THRESHOLD,
            'signal_check_interval': SIGNAL_CHECK_INTERVAL
        }
        
        # Load default configuration if it exists
        self._load_default_config_if_exists()
        
        # Daily reset
        self.last_reset_date = datetime.now().date()
        
    def start(self):
        """Start the trading bot"""
        if self.is_running:
            return False
        
        self.is_running = True
        self._schedule_tasks()
        self._log_activity("Bot started")
        return True
    
    def stop(self):
        """Stop the trading bot"""
        if not self.is_running:
            return False
        
        self.is_running = False
        schedule.clear()
        self._log_activity("Bot stopped")
        return True
    
    def _schedule_tasks(self):
        """Schedule periodic tasks"""
        # Schedule signal checking every 60 seconds for more aggressive monitoring
        schedule.every(60).seconds.do(self._check_signals)
        
        # Schedule daily reset at midnight
        schedule.every().day.at("00:00").do(self._daily_reset)
        
        # Start the scheduler in a separate thread
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def _check_signals(self):
        """Check for trading signals - runs every 60 seconds"""
        try:
            self.last_check = datetime.now()
            self._log_activity("🔍 Checking for trading signals...")
            
            signal, message = self.market_analyzer.analyze_market_signal()
            
            if signal:
                self._log_activity(f"🚨 SIGNAL DETECTED: {signal['type']} - {message}")
                # Log signal details in a cleaner format
                signal_info = f"Type: {signal['type']}, Exchanges: {', '.join(signal.get('exchanges', []))}"
                if 'avg_magnitude' in signal:
                    signal_info += f", Avg Magnitude: {signal['avg_magnitude']:.2f}%"
                self._log_activity(f"Signal details: {signal_info}")
                
                # Check if we can trade
                if self._can_trade():
                    self._log_activity("✅ Trading conditions met - executing trade...")
                    self._execute_trade_signal(signal)
                else:
                    self._log_activity("⚠️ Signal detected but cannot trade (limits reached)")
                    # Log why we can't trade
                    if self.trades_today >= self.config['max_daily_trades']:
                        self._log_activity(f"Daily trade limit reached: {self.trades_today}/{self.config['max_daily_trades']}")
                    usdc_balance = self.dex_trader.get_usdc_balance()
                    if usdc_balance < self.config['min_balance_threshold']:
                        self._log_activity(f"Low USDC balance: {usdc_balance:.2f} < {self.config['min_balance_threshold']}")
                    if usdc_balance < self.config['trade_amount']:
                        self._log_activity(f"Insufficient USDC for trade: {usdc_balance:.2f} < {self.config['trade_amount']}")
            else:
                self._log_activity(f"📊 No signal detected: {message}")
                
        except Exception as e:
            self._log_activity(f"❌ Error checking signals: {str(e)}")
            import traceback
            self._log_activity(f"Error details: {traceback.format_exc()}")
    
    def _can_trade(self):
        """Check if trading is allowed"""
        # Check daily trade limit
        if self.trades_today >= self.config['max_daily_trades']:
            return False
        
        # Check USDC balance
        usdc_balance = self.dex_trader.get_usdc_balance()
        if usdc_balance < self.config['min_balance_threshold']:
            return False
        
        # Check if we have enough USDC for the trade
        if usdc_balance < self.config['trade_amount']:
            return False
        
        return True
    
    def _execute_trade_signal(self, signal):
        """Execute trade based on signal"""
        try:
            if signal['type'] == 'simultaneous_spikes':
                # For simultaneous spikes, we'll buy CRO (expecting volatility)
                self._execute_buy_trade()
            elif signal['type'] == 'strong_upward':
                # Strong upward movement - buy CRO
                self._execute_buy_trade()
            elif signal['type'] == 'strong_downward':
                # Strong downward movement - sell CRO if we have any
                cro_balance = self.dex_trader.get_cro_balance()
                if cro_balance > 0:
                    self._execute_sell_trade()
                else:
                    self._log_activity("Strong downward signal but no CRO to sell")
            
        except Exception as e:
            self._log_activity(f"Error executing trade: {str(e)}")
            self.failed_trades += 1
    
    def _execute_buy_trade(self):
        """Execute buy CRO trade"""
        try:
            trade_amount = min(self.config['trade_amount'], self.config['max_trade_amount'])
            
            result = self.dex_trader.buy_cro_with_usdc(
                trade_amount, 
                self.config['slippage']
            )
            
            if result['success']:
                self.trades_today += 1
                self.successful_trades += 1
                self._log_activity(
                    f"Buy executed: ${trade_amount} USDC -> {result['expected_amount']:.4f} CRO "
                    f"(TX: {result['tx_hash'][:10]}...)"
                )
            else:
                self.failed_trades += 1
                self._log_activity(f"Buy failed: {result['error']}")
                
        except Exception as e:
            self.failed_trades += 1
            self._log_activity(f"Buy error: {str(e)}")
    
    def _execute_sell_trade(self):
        """Execute sell CRO trade"""
        try:
            cro_balance = self.dex_trader.get_cro_balance()
            if cro_balance <= 0:
                self._log_activity("No CRO to sell")
                return
            
            # Sell a portion of CRO balance (e.g., 50%)
            sell_amount = cro_balance * 0.5
            
            result = self.dex_trader.sell_cro_for_usdc(
                sell_amount, 
                self.config['slippage']
            )
            
            if result['success']:
                self.trades_today += 1
                self.successful_trades += 1
                self._log_activity(
                    f"Sell executed: {sell_amount:.4f} CRO -> ${result['expected_amount']:.2f} USDC "
                    f"(TX: {result['tx_hash'][:10]}...)"
                )
            else:
                self.failed_trades += 1
                self._log_activity(f"Sell failed: {result['error']}")
                
        except Exception as e:
            self.failed_trades += 1
            self._log_activity(f"Sell error: {str(e)}")
    
    def execute_manual_trade(self, action):
        """Execute manual trade (buy/sell)"""
        try:
            if action == 'buy':
                trade_amount = min(self.config['trade_amount'], self.config['max_trade_amount'])
                result = self.dex_trader.buy_cro_with_usdc(
                    trade_amount, 
                    self.config['slippage']
                )
                if result['success']:
                    self.trades_today += 1
                    self.successful_trades += 1
                    self._log_activity(f"Manual buy: ${trade_amount} USDC")
                return result
                
            elif action == 'sell':
                cro_balance = self.dex_trader.get_cro_balance()
                if cro_balance <= 0:
                    return {'success': False, 'error': 'No wrapped CRO to sell. You need to wrap your WCRO first or buy some CRO.'}
                
                # Only sell a portion of CRO balance (e.g., 50%) to avoid selling everything
                sell_amount = cro_balance * 0.5
                if sell_amount < 0.001:  # Minimum amount check
                    return {'success': False, 'error': f'CRO amount too small to sell. You have {cro_balance:.6f} CRO, but need at least 0.001 CRO to sell.'}
                
                result = self.dex_trader.sell_cro_for_usdc(
                    sell_amount, 
                    self.config['slippage']
                )
                if result['success']:
                    self.trades_today += 1
                    self.successful_trades += 1
                    self._log_activity(f"Manual sell: {sell_amount:.4f} CRO")
                return result
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def wrap_wcro_to_cro(self, amount):
        """Wrap WCRO to CRO for trading"""
        try:
            # This would require implementing a wrap function in the DEX trader
            # For now, return an informative message
            return {
                'success': False, 
                'error': 'WCRO wrapping not implemented yet. You need to manually wrap your WCRO to CRO using a DEX like VVS Finance, or buy some CRO with USDC first.'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_market_signal(self):
        """Check market signal manually"""
        return self.market_analyzer.analyze_market_signal()
    
    def force_signal_check(self):
        """Force an immediate signal check (for testing)"""
        self._log_activity("🔄 Forcing immediate signal check...")
        self._check_signals()
        return self.get_status()
    
    def get_balances(self):
        """Get wallet balances"""
        try:
            return {
                'cro': self.dex_trader.get_cro_balance(),  # Wrapped CRO for trading
                'usdc': self.dex_trader.get_usdc_balance(),
                'wcro': float(self.wallet.get_balance())  # Native WCRO balance
            }
        except Exception as e:
            raise Exception(f"Error fetching balances: {str(e)}")
    
    def get_status(self):
        """Get bot status"""
        return {
            'is_running': self.is_running,
            'last_check': self.last_check.strftime('%Y-%m-%d %H:%M:%S') if self.last_check else 'Never',
            'trades_today': self.trades_today,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'recent_activity': '\n'.join(self.recent_activity[-5:]) if self.recent_activity else 'No recent activity',
            'trade_amount': self.config['trade_amount'],
            'slippage': self.config['slippage'],
            'min_price_change': self.config['min_price_change']
        }
    
    def update_config(self, key, value):
        """Update configuration"""
        if key in self.config:
            self.config[key] = value
            self._log_activity(f"Config updated: {key} = {value}")
        else:
            raise ValueError(f"Unknown configuration key: {key}")
    
    def _daily_reset(self):
        """Reset daily counters"""
        self.trades_today = 0
        self.last_reset_date = datetime.now().date()
        self._log_activity("Daily reset completed")
    
    def _log_activity(self, message):
        """Log activity with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.recent_activity.append(log_entry)
        
        # Keep only last 20 activities
        if len(self.recent_activity) > 20:
            self.recent_activity = self.recent_activity[-20:]
        
        print(log_entry)  # Also print to console
    
    def _load_default_config_if_exists(self):
        """Load default configuration from file if it exists"""
        try:
            if os.path.exists(self.default_config_file):
                with open(self.default_config_file, 'r') as f:
                    default_config = json.load(f)
                    # Update current config with default values
                    for key, value in default_config.items():
                        if key in self.config:
                            self.config[key] = value
                    self._log_activity("Default configuration loaded from file")
        except Exception as e:
            self._log_activity(f"Error loading default config: {str(e)}")
    
    def save_as_default_config(self):
        """Save current configuration as default"""
        try:
            with open(self.default_config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self._log_activity("Current configuration saved as default")
        except Exception as e:
            raise Exception(f"Error saving default config: {str(e)}")
    
    def load_default_config(self):
        """Load default configuration from file"""
        try:
            if os.path.exists(self.default_config_file):
                with open(self.default_config_file, 'r') as f:
                    default_config = json.load(f)
                    # Update current config with default values
                    for key, value in default_config.items():
                        if key in self.config:
                            self.config[key] = value
                    self._log_activity("Default configuration loaded")
            else:
                # If no default config file exists, reset to hardcoded defaults
                self.config = {
                    'trade_amount': DEFAULT_TRADE_AMOUNT,
                    'slippage': DEFAULT_SLIPPAGE,
                    'min_price_change': MIN_PRICE_CHANGE,
                    'max_daily_trades': MAX_DAILY_TRADES,
                    'max_trade_amount': MAX_TRADE_AMOUNT,
                    'min_balance_threshold': MIN_BALANCE_THRESHOLD,
                    'signal_check_interval': SIGNAL_CHECK_INTERVAL
                }
                self._log_activity("Configuration reset to hardcoded defaults")
        except Exception as e:
            raise Exception(f"Error loading default config: {str(e)}")
    
    def is_current_config_default(self):
        """Check if current configuration matches the saved default"""
        try:
            if not os.path.exists(self.default_config_file):
                return False
            
            with open(self.default_config_file, 'r') as f:
                default_config = json.load(f)
                
            # Compare current config with default config
            for key, value in default_config.items():
                if key in self.config and self.config[key] != value:
                    return False
            return True
        except Exception:
            return False
