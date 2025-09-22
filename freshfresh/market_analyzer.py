import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from config import MIN_PRICE_CHANGE, PRICE_LOOKBACK_PERIODS, SPIKE_THRESHOLD

class MarketAnalyzer:
    def __init__(self):
        self.exchanges = {
            'kucoin': ccxt.kucoin(),
            'crypto_com': ccxt.cryptocom()
        }
        
    def get_price_data(self, symbol='CRO/USDT', timeframe='1m', limit=20):
        """Get price data from multiple exchanges"""
        price_data = {}
        
        # Use different symbols for different exchanges
        exchange_symbols = {
            'kucoin': 'CRO/USDT',
            'crypto_com': 'CRO/USDT'
        }
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                # Try the exchange-specific symbol
                exchange_symbol = exchange_symbols.get(exchange_name, symbol)
                ohlcv = exchange.fetch_ohlcv(exchange_symbol, timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                price_data[exchange_name] = df
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Error fetching data from {exchange_name}: {str(e)}")
                continue
                
        return price_data
    
    def detect_spikes(self, price_data):
        """Detect simultaneous up/down spikes across exchanges"""
        spikes = {}
        
        for exchange_name, df in price_data.items():
            if len(df) < PRICE_LOOKBACK_PERIODS:
                continue
                
            # Calculate price changes
            df['price_change'] = df['close'].pct_change() * 100
            df['price_change_abs'] = abs(df['price_change'])
            
            # Detect spikes in the last few periods
            recent_data = df.tail(PRICE_LOOKBACK_PERIODS)
            max_change = recent_data['price_change_abs'].max()
            
            if max_change >= SPIKE_THRESHOLD:
                spike_period = recent_data[recent_data['price_change_abs'] == max_change].index[0]
                spike_direction = 'up' if recent_data.loc[spike_period, 'price_change'] > 0 else 'down'
                spike_magnitude = recent_data.loc[spike_period, 'price_change']
                
                spikes[exchange_name] = {
                    'direction': spike_direction,
                    'magnitude': spike_magnitude,
                    'timestamp': recent_data.loc[spike_period, 'timestamp'],
                    'price': recent_data.loc[spike_period, 'close']
                }
        
        return spikes
    
    def analyze_market_signal(self, symbol='CRO/USDT'):
        """Analyze market for trading signals"""
        try:
            # Get price data from multiple exchanges
            price_data = self.get_price_data(symbol)
            
            if not price_data:
                return None, "No price data available"
            
            # Detect spikes
            spikes = self.detect_spikes(price_data)
            
            if not spikes:
                return None, "No significant spikes detected"
            
            # Analyze spike patterns
            up_spikes = [s for s in spikes.values() if s['direction'] == 'up']
            down_spikes = [s for s in spikes.values() if s['direction'] == 'down']
            
            # Check for simultaneous up/down spikes (more aggressive detection)
            if len(up_spikes) >= 1 and len(down_spikes) >= 1:
                # Calculate average magnitudes
                avg_up_magnitude = np.mean([s['magnitude'] for s in up_spikes])
                avg_down_magnitude = np.mean([s['magnitude'] for s in down_spikes])
                
                # Check if magnitudes are significant (lowered threshold for more aggressive trading)
                if avg_up_magnitude >= MIN_PRICE_CHANGE * 0.8 and avg_down_magnitude >= MIN_PRICE_CHANGE * 0.8:
                    signal = {
                        'type': 'simultaneous_spikes',
                        'up_spikes': up_spikes,
                        'down_spikes': down_spikes,
                        'avg_up_magnitude': avg_up_magnitude,
                        'avg_down_magnitude': avg_down_magnitude,
                        'timestamp': datetime.now(),
                        'exchanges': list(spikes.keys())
                    }
                    return signal, f"Simultaneous up/down spikes detected (Up: {avg_up_magnitude:.2f}%, Down: {avg_down_magnitude:.2f}%)"
            
            # Check for strong unidirectional movement (more aggressive detection)
            elif len(up_spikes) >= 1:  # Lowered from 2 to 1 for more sensitivity
                avg_magnitude = np.mean([s['magnitude'] for s in up_spikes])
                if avg_magnitude >= MIN_PRICE_CHANGE * 1.2:  # Lowered threshold for more aggressive trading
                    signal = {
                        'type': 'strong_upward',
                        'spikes': up_spikes,
                        'avg_magnitude': avg_magnitude,
                        'timestamp': datetime.now(),
                        'exchanges': list(spikes.keys())
                    }
                    return signal, f"Strong upward movement detected ({avg_magnitude:.2f}%)"
            
            elif len(down_spikes) >= 1:  # Lowered from 2 to 1 for more sensitivity
                avg_magnitude = np.mean([s['magnitude'] for s in down_spikes])
                if avg_magnitude >= MIN_PRICE_CHANGE * 1.2:  # Lowered threshold for more aggressive trading
                    signal = {
                        'type': 'strong_downward',
                        'spikes': down_spikes,
                        'avg_magnitude': avg_magnitude,
                        'timestamp': datetime.now(),
                        'exchanges': list(spikes.keys())
                    }
                    return signal, f"Strong downward movement detected ({avg_magnitude:.2f}%)"
            
            return None, "No significant trading signals"
            
        except Exception as e:
            return None, f"Error analyzing market: {str(e)}"
    
    def get_current_price(self, symbol='CRO/USDT'):
        """Get current price from multiple exchanges"""
        prices = {}
        
        # Use different symbols for different exchanges
        exchange_symbols = {
            'kucoin': 'CRO/USDT',
            'crypto_com': 'CRO/USDT'
        }
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                # Try the exchange-specific symbol
                exchange_symbol = exchange_symbols.get(exchange_name, symbol)
                ticker = exchange.fetch_ticker(exchange_symbol)
                prices[exchange_name] = {
                    'price': ticker['last'],
                    'timestamp': datetime.now()
                }
                time.sleep(0.1)
            except Exception as e:
                print(f"Error fetching price from {exchange_name}: {str(e)}")
                continue
                
        return prices
