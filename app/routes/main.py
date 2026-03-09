from flask import jsonify
from app.utils.alpaca import get_historical_bars

@bp.route('/api/historical/<symbol>')
@login_required
def api_historical(symbol):
    bars = get_historical_bars(symbol, timeframe='day', limit=30)
    if isinstance(bars, dict) and 'error' in bars:
        return jsonify({'error': bars['error']}), 400
    return jsonify(bars)
