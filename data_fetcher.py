"""
Fetches real-time and historical stock data from Yahoo Finance
with mock fallback to always provide chart data.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import random
import config

class DataFetcher:
    def __init__(self, symbol=config.STOCK_SYMBOL):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.historical_data = []
        
    def fetch_historical_data(self, days=config.HISTORICAL_DAYS):
        """Fetch historical data – fallback to mock if fails"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            data = self.ticker.history(start=start_date, end=end_date, interval="5m")
            if data.empty:
                data = self.ticker.history(period="5d", interval="5m")
            if not data.empty:
                candles = []
                for index, row in data.iterrows():
                    candles.append({
                        "time": int(index.timestamp()),
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0
                    })
                self.historical_data = candles
                print(f"✓ Fetched {len(candles)} candles for {self.symbol}")
                return candles
        except Exception as e:
            print(f"Fetch error: {e}")
        
        # Fallback: generate mock candles so chart always shows something
        print(f"⚠️ Using mock candles for {self.symbol}")
        candles = []
        now = datetime.now()
        price = 100.0
        for i in range(100):
            ts = now - timedelta(minutes=5*i)
            price += random.uniform(-1, 1)
            candles.append({
                "time": int(ts.timestamp()),
                "open": round(price - 0.2, 2),
                "high": round(price + 0.3, 2),
                "low": round(price - 0.3, 2),
                "close": round(price, 2),
                "volume": random.randint(1000, 10000)
            })
        self.historical_data = candles[::-1]
        return self.historical_data
    
    def get_live_quote(self):
        """Get current live price with fallback"""
        try:
            data = self.ticker.history(period="1d", interval="1m")
            if not data.empty:
                return {
                    "price": float(data['Close'].iloc[-1]),
                    "volume": int(data['Volume'].iloc[-1]) if not pd.isna(data['Volume'].iloc[-1]) else 0,
                    "timestamp": int(datetime.now().timestamp())
                }
        except:
            pass
        
        # Fallback: random walk for demo
        if not hasattr(self, 'mock_price'):
            self.mock_price = 100.0
        self.mock_price += random.uniform(-0.5, 0.5)
        self.mock_price = max(self.mock_price, 10)
        return {
            "price": round(self.mock_price, 2),
            "volume": random.randint(1000, 50000),
            "timestamp": int(datetime.now().timestamp())
        }
    
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