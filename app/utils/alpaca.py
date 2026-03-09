import os
from alpaca_trade_api import REST
from dotenv import load_dotenv

load_dotenv()

def get_alpaca_client(api_key=None, secret_key=None):
    """
    Returns an Alpaca REST client.
    If api_key and secret_key are provided, use them.
    Otherwise, use the default from environment variables.
    """
    if api_key and secret_key:
        return REST(api_key, secret_key, base_url=os.getenv('ALPACA_BASE_URL'))
    else:
        return REST(
            os.getenv('ALPACA_API_KEY'),
            os.getenv('ALPACA_SECRET_KEY'),
            base_url=os.getenv('ALPACA_BASE_URL')
        )

def get_stock_quote(symbol, client=None):
    """Get the latest trade (quote) for a symbol."""
    if not client:
        client = get_alpaca_client()
    try:
        trade = client.get_last_trade(symbol)
        return {
            'symbol': symbol,
            'price': trade.price,
            'size': trade.size,
            'timestamp': trade.timestamp.isoformat() if hasattr(trade.timestamp, 'isoformat') else str(trade.timestamp)
        }
    except Exception as e:
        return {'error': str(e)}

def get_historical_bars(symbol, timeframe='day', limit=30):
    """
    Get historical bars for a symbol.
    timeframe: 'minute', '1Min', '5Min', '15Min', 'day', etc.
    limit: number of bars.
    Returns a list of dicts with keys: time, open, high, low, close, volume.
    """
    client = get_alpaca_client()
    try:
        bars = client.get_bars(symbol, timeframe, limit=limit).df
        # Reset index to make timestamp a column
        bars.reset_index(inplace=True)
        # Convert timestamp to string for JSON serialization
        bars['time'] = bars['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        # Select and rename columns
        result = bars[['time', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
        return result
    except Exception as e:
        return {'error': str(e)}
