"""
Stock/Crypto Predictor – High Sensitivity Version
"""

import numpy as np
import config

class StockPredictor:
    def __init__(self):
        self.short_ema = config.SHORT_EMA_PERIOD
        self.long_ema = config.LONG_EMA_PERIOD

    def calculate_ema(self, prices, period):
        if len(prices) < period:
            return []
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]
        for i in range(period, len(prices)):
            ema.append((prices[i] - ema[-1]) * multiplier + ema[-1])
        return ema

    def calculate_rsi(self, prices, period=10):
        if len(prices) < period + 1:
            return 50
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def detect_candlestick_pattern(self, candle):
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        total_range = candle['high'] - candle['low']
        if total_range == 0:
            return "neutral"
        if body <= total_range * 0.1:
            return "doji"
        if lower_shadow >= body * 2 and upper_shadow < body * 0.5:
            return "hammer"
        if upper_shadow >= body * 2 and lower_shadow < body * 0.5:
            return "shooting_star"
        return "neutral"

    def predict(self, closing_prices, last_candle):
        if len(closing_prices) < self.long_ema + 3:
            return "hold"
        
        # Momentum
        recent_change = 0
        if len(closing_prices) >= 3:
            recent_change = (closing_prices[-1] - closing_prices[-3]) / closing_prices[-3]
        
        # EMA crossover
        ema_short = self.calculate_ema(closing_prices, self.short_ema)
        ema_long = self.calculate_ema(closing_prices, self.long_ema)
        ema_signal = "hold"
        if len(ema_short) >= 2 and len(ema_long) >= 2:
            if ema_short[-2] <= ema_long[-2] and ema_short[-1] > ema_long[-1]:
                ema_signal = "buy"
            elif ema_short[-2] >= ema_long[-2] and ema_short[-1] < ema_long[-1]:
                ema_signal = "sell"
        
        # RSI
        rsi = self.calculate_rsi(closing_prices, period=10)
        rsi_signal = "hold"
        if rsi < 45:
            rsi_signal = "buy"
        elif rsi > 55:
            rsi_signal = "sell"
        
        # Candlestick pattern
        pattern = self.detect_candlestick_pattern(last_candle)
        pattern_signal = "hold"
        if pattern == "hammer":
            pattern_signal = "buy"
        elif pattern == "shooting_star":
            pattern_signal = "sell"
        
        # Momentum
        momentum_signal = "hold"
        if recent_change > 0.001:
            momentum_signal = "buy"
        elif recent_change < -0.001:
            momentum_signal = "sell"
        
        signals = {"buy":0, "sell":0, "hold":0}
        signals[ema_signal] += 2
        signals[rsi_signal] += 3
        signals[pattern_signal] += 1
        signals[momentum_signal] += 4
        
        if signals["buy"] > signals["sell"] and signals["buy"] > signals["hold"]:
            return "buy"
        elif signals["sell"] > signals["buy"] and signals["sell"] > signals["hold"]:
            return "sell"
        return "hold"