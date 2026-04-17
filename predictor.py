"""
Stock/Crypto Predictor – High Sensitivity Version
Generates frequent BUY/SELL signals using:
- Short-term EMA crossover
- RSI with wider thresholds
- Candlestick pattern detection
- Price momentum (0.1% change)
"""

import numpy as np
import config

class StockPredictor:
    def __init__(self):
        self.short_ema = config.SHORT_EMA_PERIOD   # 5
        self.long_ema = config.LONG_EMA_PERIOD     # 20

    def calculate_ema(self, prices, period):
        """
        Calculate Exponential Moving Average
        """
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema = []
        # Start with SMA
        sma = sum(prices[:period]) / period
        ema.append(sma)
        
        for i in range(period, len(prices)):
            ema_value = (prices[i] - ema[-1]) * multiplier + ema[-1]
            ema.append(ema_value)
        
        return ema

    def calculate_rsi(self, prices, period=10):
        """
        Calculate Relative Strength Index with shorter period for more signals
        """
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
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def detect_candlestick_pattern(self, candle):
        """
        Detect basic candlestick patterns
        """
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        total_range = candle['high'] - candle['low']
        
        if total_range == 0:
            return "neutral"
        
        # Doji (indecision)
        if body <= total_range * 0.1:
            return "doji"
        
        # Hammer (bullish reversal)
        if lower_shadow >= body * 2 and upper_shadow < body * 0.5:
            return "hammer"
        
        # Shooting Star (bearish reversal)
        if upper_shadow >= body * 2 and lower_shadow < body * 0.5:
            return "shooting_star"
        
        return "neutral"

    def predict(self, closing_prices, last_candle):
        """
        Generate prediction (buy/sell/hold) with higher sensitivity.
        Returns 'buy', 'sell', or 'hold'.
        """
        if len(closing_prices) < self.long_ema + 3:
            return "hold"
        
        # 1. Price momentum (very sensitive – 0.1% change triggers signal)
        recent_change = 0
        if len(closing_prices) >= 3:
            recent_change = (closing_prices[-1] - closing_prices[-3]) / closing_prices[-3]
        
        # 2. EMA crossover signal
        ema_short = self.calculate_ema(closing_prices, self.short_ema)
        ema_long = self.calculate_ema(closing_prices, self.long_ema)
        
        ema_signal = "hold"
        if len(ema_short) >= 2 and len(ema_long) >= 2:
            if ema_short[-2] <= ema_long[-2] and ema_short[-1] > ema_long[-1]:
                ema_signal = "buy"
            elif ema_short[-2] >= ema_long[-2] and ema_short[-1] < ema_long[-1]:
                ema_signal = "sell"
        
        # 3. RSI (wider thresholds for more signals)
        rsi = self.calculate_rsi(closing_prices, period=10)
        rsi_signal = "hold"
        if rsi < 45:      # Oversold threshold lowered
            rsi_signal = "buy"
        elif rsi > 55:    # Overbought threshold lowered
            rsi_signal = "sell"
        
        # 4. Candlestick pattern
        pattern = self.detect_candlestick_pattern(last_candle)
        pattern_signal = "hold"
        if pattern == "hammer":
            pattern_signal = "buy"
        elif pattern == "shooting_star":
            pattern_signal = "sell"
        
        # 5. Momentum signal (very sensitive – 0.1% move)
        momentum_signal = "hold"
        if recent_change > 0.001:     # 0.1% up
            momentum_signal = "buy"
        elif recent_change < -0.001:   # 0.1% down
            momentum_signal = "sell"
        
        # Weighted voting – momentum and RSI get highest weights
        signals = {"buy": 0, "sell": 0, "hold": 0}
        signals[ema_signal] += 2
        signals[rsi_signal] += 3
        signals[pattern_signal] += 1
        signals[momentum_signal] += 4   # highest weight for quick reactions
        
        # Decision
        if signals["buy"] > signals["sell"] and signals["buy"] > signals["hold"]:
            return "buy"
        elif signals["sell"] > signals["buy"] and signals["sell"] > signals["hold"]:
            return "sell"
        return "hold"