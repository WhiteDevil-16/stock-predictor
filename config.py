"""
Configuration settings for the stock predictor
"""

# Stock settings - You can change this to any symbol
STOCK_SYMBOL = "AAPL"  # Default symbol
UPDATE_INTERVAL_SECONDS = 2

# Technical indicator parameters
SHORT_EMA_PERIOD = 5
LONG_EMA_PERIOD = 20
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Historical data settings
HISTORICAL_DAYS = 30
MAX_CANDLES_TO_KEEP = 200

# Accuracy tracking
PREDICTION_LOOKBACK_INTERVALS = 10
PRICE_CHANGE_THRESHOLD = 0.005

# Server settings
HOST = "127.0.0.1"
PORT = 8000

# List of stocks to pre-load (US, Indian, Crypto)
DEFAULT_STOCKS = [
    # US Stocks
    "AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "JPM",
    # Indian Stocks (NSE)
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "HINDUNILVR.NS", "WIPRO.NS",
    # Cryptocurrencies
    "BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD", "ADA-USD", 
    "SOL-USD", "DOT-USD", "LTC-USD", "AVAX-USD", "MATIC-USD"
]