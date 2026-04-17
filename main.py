"""
Main FastAPI application - Multi-Stock Predictor (FULLY FIXED)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
import config
from data_fetcher import DataFetcher
from predictor import StockPredictor
from accuracy_tracker import AccuracyTracker
import config

# Global state (module level)
stock_data = {}
current_symbol = config.STOCK_SYMBOL
manager = None
update_task = None

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

def get_or_create_stock_data(symbol):
    """Get or initialize data structures for a given stock symbol"""
    if symbol not in stock_data:
        print(f"  → Initializing data for {symbol}...")
        stock_data[symbol] = {
            "fetcher": DataFetcher(symbol),
            "predictor": StockPredictor(),
            "tracker": AccuracyTracker(),
            "historical_candles": [],
            "last_candle": None,
            "last_update_time": None
        }
        # Fetch historical data
        candles = stock_data[symbol]["fetcher"].fetch_historical_data()
        stock_data[symbol]["historical_candles"] = candles
        if candles:
            stock_data[symbol]["last_candle"] = candles[-1]
            print(f"  ✓ {symbol}: Loaded {len(candles)} candles, price: ${candles[-1]['close']:.2f}")
        else:
            print(f"  ⚠ {symbol}: No historical data yet")
    return stock_data[symbol]

async def update_stock_data(symbol):
    """Update data for a specific stock"""
    data = get_or_create_stock_data(symbol)
    fetcher = data["fetcher"]
    predictor = data["predictor"]
    tracker = data["tracker"]
    historical_candles = data["historical_candles"]
    last_candle = data["last_candle"]
    
    quote = fetcher.get_live_quote()
    if quote and quote['price'] > 0:
        current_time = datetime.now().timestamp()
        
        # Update or create candle
        if last_candle and (current_time - last_candle['time']) < 120:
            last_candle = fetcher.update_candle(last_candle, quote)
        else:
            if last_candle:
                historical_candles.append(last_candle)
            last_candle = fetcher.create_new_candle(quote)
            if len(historical_candles) > config.MAX_CANDLES_TO_KEEP:
                historical_candles = historical_candles[-config.MAX_CANDLES_TO_KEEP:]
        
        # Generate prediction
        if len(historical_candles) > 5:
            closing_prices = [c['close'] for c in historical_candles] + [last_candle['close']]
            prediction = predictor.predict(closing_prices, last_candle)
        else:
            prediction = "hold"
        
        # Track accuracy
        if tracker.last_price is not None:
            tracker.add_prediction(prediction, quote['price'])
        tracker.update_accuracy(quote['price'])
        tracker.last_price = quote['price']
        accuracy = tracker.get_recent_accuracy()
        
        # Save updated state
        data["historical_candles"] = historical_candles
        data["last_candle"] = last_candle
        data["last_update_time"] = datetime.now()
        
        # Prepare update message
        all_candles = historical_candles + ([last_candle] if last_candle else [])
        return {
            "symbol": symbol,
            "price": round(quote['price'], 2),
            "timestamp": quote['timestamp'],
            "prediction": prediction,
            "accuracy": round(accuracy, 1),
            "lastCandle": last_candle,
            "historicalData": all_candles[-100:]
        }
    return None

async def periodic_updates():
    """Background task to update the current stock and broadcast"""
    global current_symbol
    while True:
        await asyncio.sleep(config.UPDATE_INTERVAL_SECONDS)
        try:
            update = await update_stock_data(current_symbol)
            if update and manager:
                await manager.broadcast(update)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {current_symbol}: ${update['price']:.2f} | {update['prediction'].upper()} | {update['accuracy']:.1f}%")
            elif not update:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ No data for {current_symbol}")
        except Exception as e:
            print(f"Update error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager, update_task, current_symbol, stock_data
    
    manager = ConnectionManager()
    
    print(f"\n{'='*60}")
    print(f"🚀 MULTI-STOCK PREDICTOR STARTED")
    print(f"{'='*60}")
    
    # Pre-load popular stocks
    default_stocks = config.DEFAULT_STOCKS
    print(f"📊 Pre-loading {len(default_stocks)} stocks...")
    for sym in default_stocks:
        get_or_create_stock_data(sym)
    
    # Start background updater
    update_task = asyncio.create_task(periodic_updates())
    
    print(f"\n✓ Server: http://{config.HOST}:{config.PORT}")
    print(f"✓ Updates: Every {config.UPDATE_INTERVAL_SECONDS} seconds")
    print(f"✓ Active stock: {current_symbol}")
    print(f"{'='*60}\n")
    
    yield
    
    update_task.cancel()
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: static/index.html not found</h1>")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_symbol  # CRITICAL: This fixes the scope error
    
    await manager.connect(websocket)
    print(f"📱 Client connected (Total: {len(manager.active_connections)})")
    
    # Send initial data for current stock
    try:
        data = stock_data.get(current_symbol)
        if data and data["last_candle"]:
            quote = data["fetcher"].get_live_quote()
            if quote and quote['price'] > 0:
                init_msg = {
                    "symbol": current_symbol,
                    "price": round(quote['price'], 2),
                    "timestamp": quote['timestamp'],
                    "prediction": "hold",
                    "accuracy": 0,
                    "lastCandle": data["last_candle"],
                    "historicalData": (data["historical_candles"] + [data["last_candle"]])[-100:]
                }
                await websocket.send_json(init_msg)
                print(f"  → Sent initial data for {current_symbol}: ${quote['price']:.2f}")
            else:
                # Fallback: send last known candle data
                fallback_msg = {
                    "symbol": current_symbol,
                    "price": round(data["last_candle"]["close"], 2),
                    "timestamp": int(datetime.now().timestamp()),
                    "prediction": "hold",
                    "accuracy": 0,
                    "lastCandle": data["last_candle"],
                    "historicalData": (data["historical_candles"] + [data["last_candle"]])[-100:]
                }
                await websocket.send_json(fallback_msg)
                print(f"  → Sent fallback data for {current_symbol}")
    except Exception as e:
        print(f"  ✗ Init send error: {e}")
    
    # Handle incoming messages (stock change requests)
    try:
        while True:
            message = await websocket.receive_text()
            if message.startswith("STOCK:"):
                new_symbol = message.split(":")[1].strip().upper()
                if new_symbol != current_symbol:
                    old_symbol = current_symbol
                    current_symbol = new_symbol  # This now works because of 'global current_symbol'
                    print(f"🔄 Switching stock: {old_symbol} → {current_symbol}")
                    
                    # Get data for new stock (will initialize if needed)
                    data = get_or_create_stock_data(current_symbol)
                    
                    # Send immediate update for new stock
                    update = await update_stock_data(current_symbol)
                    if update:
                        await websocket.send_json(update)
                        print(f"  ✓ Sent update for {current_symbol}: ${update['price']:.2f}")
                    elif data and data["last_candle"]:
                        # Fallback to last known candle
                        fallback = {
                            "symbol": current_symbol,
                            "price": round(data["last_candle"]["close"], 2),
                            "timestamp": int(datetime.now().timestamp()),
                            "prediction": "hold",
                            "accuracy": 0,
                            "lastCandle": data["last_candle"],
                            "historicalData": (data["historical_candles"] + [data["last_candle"]])[-100:]
                        }
                        await websocket.send_json(fallback)
                        print(f"  ✓ Sent fallback for {current_symbol}")
                    else:
                        print(f"  ✗ No data available for {current_symbol}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"📱 Client disconnected (Total: {len(manager.active_connections)})")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="warning")