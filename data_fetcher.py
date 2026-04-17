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
        # Try real data first
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
                print(f"✓ Real candles for {self.symbol}: {len(candles)}")
                return candles
        except Exception as e:
            print(f"Real data error for {self.symbol}: {e}")
        
        # ----- MOCK CANDLES (ensures chart always shows) -----
        print(f"⚠️ Generating mock candles for {self.symbol}")
        candles = []
        now = datetime.now()
        base_price = 100.0
        # Use different base price for different symbols to avoid flat lines
        if self.symbol == "BTC-USD":
            base_price = 76000
        elif self.symbol == "ETH-USD":
            base_price = 3500
        elif self.symbol == "DOGE-USD":
            base_price = 0.15
        elif self.symbol == "AAPL":
            base_price = 260
        elif self.symbol == "TSLA":
            base_price = 180
        else:
            base_price = 100
            
        price = base_price
        for i in range(100):
            ts = now - timedelta(minutes=5*i)
            # Random walk
            price += random.uniform(-price*0.02, price*0.02)
            price = max(price, base_price*0.5)
            candles.append({
                "time": int(ts.timestamp()),
                "open": round(price - price*0.005, 2),
                "high": round(price + price*0.01, 2),
                "low": round(price - price*0.01, 2),
                "close": round(price, 2),
                "volume": random.randint(1000, 100000)
            })
        self.historical_data = candles[::-1]
        return self.historical_data
    
    def get_live_quote(self):
        # Try real quote
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
        # Mock quote
        if not hasattr(self, 'mock_price'):
            self.mock_price = 76000 if self.symbol == "BTC-USD" else 260
        self.mock_price += random.uniform(-self.mock_price*0.005, self.mock_price*0.005)
        self.mock_price = max(self.mock_price, 10)
        return {
            "price": round(self.mock_price, 2),
            "volume": random.randint(1000, 50000),
            "timestamp": int(datetime.now().timestamp())
        }
    
    def update_candle(self, current_candle, new_quote):
        if current_candle and new_quote:
            current_candle['high'] = max(current_candle['high'], new_quote['price'])
            current_candle['low'] = min(current_candle['low'], new_quote['price'])
            current_candle['close'] = new_quote['price']
            current_candle['volume'] += new_quote['volume']
        return current_candle
    
    def create_new_candle(self, quote):
        return {
            "time": quote['timestamp'],
            "open": quote['price'],
            "high": quote['price'],
            "low": quote['price'],
            "close": quote['price'],
            "volume": quote['volume']
        }