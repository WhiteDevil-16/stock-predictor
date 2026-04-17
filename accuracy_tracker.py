"""
Tracks prediction accuracy by comparing with actual price movements
"""

import config
from datetime import datetime

class AccuracyTracker:
    def __init__(self):
        self.predictions = []  # List of prediction records
        self.last_price = None
        
    def add_prediction(self, action, price):
        """
        Add a new prediction to track
        """
        prediction = {
            "timestamp": datetime.now(),
            "action": action,
            "price_at_prediction": price,
            "completed": False,
            "correct": False,
            "target_price": None
        }
        self.predictions.append(prediction)
        
        # Keep only last 100 predictions
        if len(self.predictions) > 100:
            self.predictions = self.predictions[-100:]
        
        return prediction
    
    def update_accuracy(self, current_price):
        """
        Update accuracy by comparing predictions with actual price movement
        """
        if len(self.predictions) == 0:
            return
        
        for pred in self.predictions:
            if not pred["completed"]:
                # Check if enough time has passed (based on intervals)
                time_diff = (datetime.now() - pred["timestamp"]).total_seconds()
                expected_time = config.UPDATE_INTERVAL_SECONDS * config.PREDICTION_LOOKBACK_INTERVALS
                
                if time_diff >= expected_time:
                    # Determine actual outcome based on price change
                    price_change = (current_price - pred["price_at_prediction"]) / pred["price_at_prediction"]
                    
                    actual_outcome = "hold"
                    if price_change > config.PRICE_CHANGE_THRESHOLD:
                        actual_outcome = "buy"
                    elif price_change < -config.PRICE_CHANGE_THRESHOLD:
                        actual_outcome = "sell"
                    
                    # Check if prediction was correct
                    pred["correct"] = (pred["action"] == actual_outcome)
                    pred["completed"] = True
                    pred["target_price"] = current_price
    
    def get_accuracy_percentage(self):
        """
        Calculate current accuracy percentage based on completed predictions
        """
        completed = [p for p in self.predictions if p["completed"]]
        if len(completed) == 0:
            return 0.0
        
        correct_count = sum(1 for p in completed if p["correct"])
        accuracy = (correct_count / len(completed)) * 100
        return accuracy
    
    def get_recent_accuracy(self, lookback=50):
        """
        Get accuracy for most recent N predictions
        """
        recent = self.predictions[-lookback:]
        completed = [p for p in recent if p["completed"]]
        
        if len(completed) == 0:
            return 0.0
        
        correct_count = sum(1 for p in completed if p["correct"])
        accuracy = (correct_count / len(completed)) * 100
        return accuracy