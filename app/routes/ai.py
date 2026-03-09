from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.utils.ai_model import train_model_for_symbol, predict_for_symbol, load_model_for_symbol
from app.utils.alpaca import get_historical_bars
import pandas as pd

bp = Blueprint('ai', __name__, url_prefix='/ai')

@bp.route('/predict/<symbol>')
@login_required
def predict(symbol):
    """
    Return prediction for a symbol.
    If model doesn't exist, returns a message.
    """
    prob_up, pred, error = predict_for_symbol(symbol)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({
        'symbol': symbol,
        'probability_up': prob_up,
        'prediction': 'UP' if pred == 1 else 'DOWN'
    })

@bp.route('/train/<symbol>', methods=['POST'])
@login_required
def train(symbol):
    """
    Train a model for a symbol. This could be slow, so in production you'd do this asynchronously.
    For now, we'll do it synchronously.
    """
    try:
        model, acc = train_model_for_symbol(symbol)
        return jsonify({'message': f'Model trained for {symbol}', 'accuracy': acc})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/status/<symbol>')
@login_required
def status(symbol):
    """
    Check if a model exists for a symbol.
    """
    model, features = load_model_for_symbol(symbol)
    if model:
        return jsonify({'trained': True})
    else:
        return jsonify({'trained': False})
