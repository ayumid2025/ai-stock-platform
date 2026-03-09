from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio
from app.utils.alpaca import get_stock_quote
import threading
import time

# Store active rooms (symbols being watched) - simple approach
# In production, use a more robust structure (Redis, etc.)
active_rooms = set()
price_update_thread_running = False

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # You could send initial data or just acknowledge

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('subscribe')
def handle_subscribe(data):
    """Client subscribes to a stock symbol for real-time updates."""
    symbol = data.get('symbol')
    if symbol:
        join_room(symbol)
        print(f'Client subscribed to {symbol}')
        # Optionally send current price immediately
        quote = get_stock_quote(symbol)
        if 'error' not in quote:
            emit('price_update', quote, room=symbol)

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    symbol = data.get('symbol')
    if symbol:
        leave_room(symbol)
        print(f'Client unsubscribed from {symbol}')

def price_update_worker():
    """Background thread that fetches prices for active symbols and emits updates."""
    global price_update_thread_running
    if price_update_thread_running:
        return
    price_update_thread_running = True
    while True:
        try:
            # Get all rooms (symbols) that have clients
            # SocketIO provides a way to get rooms, but we need to track active symbols ourselves.
            # For simplicity, we'll maintain a set of symbols that have at least one subscriber.
            # We'll update this set based on join/leave events.
            # However, SocketIO doesn't expose a direct way to list rooms with clients.
            # Alternative: use a dict mapping symbol to last update time, and emit to all symbols that have any client.
            # We'll rely on the fact that when a client subscribes, they join a room named after the symbol.
            # To get rooms, we can use socketio.server.manager.rooms, but that's internal.
            # Simpler: maintain our own set of active symbols.
            # We'll update active_rooms in handle_subscribe and handle_unsubscribe.
            symbols = list(active_rooms)
            for symbol in symbols:
                quote = get_stock_quote(symbol)
                if 'error' not in quote:
                    socketio.emit('price_update', quote, room=symbol)
                    print(f'Emitted price update for {symbol}: ${quote["price"]}')
            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            print(f"Error in price update worker: {e}")
            time.sleep(5)

# Start background thread when the first client connects
# We'll start it from the first connection event
@socketio.on('connect')
def on_connect():
    # Start background thread if not already running
    if not hasattr(socketio, 'price_thread') or not socketio.price_thread.is_alive():
        socketio.price_thread = threading.Thread(target=price_update_worker, daemon=True)
        socketio.price_thread.start()
        print("Price update thread started")
