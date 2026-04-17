"""
Fetches real-time and historical stock data from Yahoo Finance - CORRECTED
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import config

class DataFetcher:
    def __init__(self, symbol=config.STOCK_SYMBOL):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.historical_data = []
        
    def fetch_historical_data(self, days=config.HISTORICAL_DAYS):
        """Fetch historical minute-level data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            print(f"Fetching {self.symbol} historical data...")
            
            # Try to get data with 5m interval (more reliable than 1m)
            data = self.ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval="5m"
            )
            
            if data.empty:
                # Fallback to 1d data if minute data not available
                print("No minute data, using daily data...")
                data = self.ticker.history(period=f"{days}d", interval="1d")
            
            if data.empty:
                print("No historical data found")
                return []
            
            # Convert to list of dictionaries
            candles = []
            for index, row in data.iterrows():
                # Convert pandas timestamp to Unix timestamp
                if hasattr(index, 'timestamp'):
                    timestamp = int(index.timestamp())
                else:
                    timestamp = int(datetime.now().timestamp())
                
                candle = {
                    "time": timestamp,
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume']) if pd.notna(row['Volume']) else 0
                }
                candles.append(candle)
            
            self.historical_data = candles
            print(f"✓ Fetched {len(candles)} candles for {self.symbol}")
            return candles
            
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_live_quote(self):
        """Get current live price"""
        try:
            # Get the latest quote
            data = self.ticker.history(period="1d", interval="1m")
            
            if data.empty:
                # Try with 5m interval
                data = self.ticker.history(period="1d", interval="5m")
            
            if not data.empty:
                last_row = data.iloc[-1]
                price = float(last_row['Close'])
                volume = int(last_row['Volume']) if pd.notna(last_row['Volume']) else 0
                
                if price > 0:
                    return {
                        "price": price,
                        "volume": volume,
                        "timestamp": int(datetime.now().timestamp())
                    }
            
            # Alternative: use fast_info
            try:
                fast_info = self.ticker.fast_info
                if hasattr(fast_info, 'last_price') and fast_info.last_price:
                    return {
                        "price": float(fast_info.last_price),
                        "volume": 0,
                        "timestamp": int(datetime.now().timestamp())
                    }
            except:
                pass
            
            print(f"Warning: Could not get live quote for {self.symbol}")
            return None
            
        except Exception as e:
            print(f"Quote error: {e}")
            return None
    
    def update_candle(self, current_candle, new_quote):
        """Update current minute candle"""
        if current_candle and new_quote:
            current_candle['high'] = max(current_candle['high'], new_quote['price'])
            current_candle['low'] = min(current_candle['low'], new_quote['price'])
            current_candle['close'] = new_quote['price']
            current_candle['volume'] += new_quote['volume']
        return current_candle
    
    def create_new_candle(self, quote):
        """Create new candle for next minute"""
        return {
            "time": quote['timestamp'],
            "open": quote['price'],
            "high": quote['price'],
            "low": quote['price'],
            "close": quote['price'],
            "volume": quote['volume']
        }