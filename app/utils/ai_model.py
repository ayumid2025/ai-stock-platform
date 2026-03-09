import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os
from app.utils.alpaca import get_historical_bars

# Directory to store trained models
MODEL_DIR = 'app/models'
os.makedirs(MODEL_DIR, exist_ok=True)

def engineer_features(df):
    """
    Add technical indicators as features for prediction.
    Expects a DataFrame with columns: time, open, high, low, close, volume.
    Returns a new DataFrame with features and a target column (1 if next close > current close, else 0).
    """
    df = df.copy()
    # Price-based features
    df['returns'] = df['close'].pct_change()
    df['sma_5'] = df['close'].rolling(window=5).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_diff'] = df['macd'] - df['macd_signal']
    
    # Volatility
    df['high_low_pct'] = (df['high'] - df['low']) / df['close'] * 100
    df['close_open_pct'] = (df['close'] - df['open']) / df['open'] * 100
    
    # Volume features
    df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
    
    # Target: 1 if next day's close is higher than today's close, else 0
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    # Drop NaN values created by rolling windows and shifting
    df.dropna(inplace=True)
    return df

def train_model_for_symbol(symbol, limit=500):
    """
    Fetch historical data for a symbol, engineer features, train a Random Forest model,
    and save it to disk. Returns the model and its accuracy on test set.
    """
    print(f"Training model for {symbol}...")
    bars = get_historical_bars(symbol, timeframe='day', limit=limit)
    if isinstance(bars, dict) and 'error' in bars:
        raise Exception(f"Error fetching data: {bars['error']}")
    
    df = pd.DataFrame(bars)
    df = engineer_features(df)
    
    # Define features (all columns except 'target', 'time')
    feature_cols = [col for col in df.columns if col not in ['target', 'time']]
    X = df[feature_cols]
    y = df['target']
    
    # Split chronologically (don't shuffle time series)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model accuracy for {symbol}: {acc:.2f}")
    
    # Save model and feature columns
    model_path = os.path.join(MODEL_DIR, f"{symbol}_model.pkl")
    joblib.dump(model, model_path)
    
    # Save feature columns (needed for prediction)
    feat_path = os.path.join(MODEL_DIR, f"{symbol}_features.pkl")
    joblib.dump(feature_cols, feat_path)
    
    return model, acc

def load_model_for_symbol(symbol):
    """
    Load a trained model and its feature columns for a symbol.
    Returns (model, feature_cols) or (None, None) if not found.
    """
    model_path = os.path.join(MODEL_DIR, f"{symbol}_model.pkl")
    feat_path = os.path.join(MODEL_DIR, f"{symbol}_features.pkl")
    if os.path.exists(model_path) and os.path.exists(feat_path):
        model = joblib.load(model_path)
        features = joblib.load(feat_path)
        return model, features
    return None, None

def predict_for_symbol(symbol, df_latest=None):
    """
    Make a prediction for the next day's direction for a symbol.
    If df_latest is not provided, fetches the latest data from Alpaca.
    Returns probability of up move and the prediction (0/1).
    """
    model, features = load_model_for_symbol(symbol)
    if model is None:
        return None, None, "Model not trained yet"
    
    if df_latest is None:
        # Fetch the most recent data to compute features
        bars = get_historical_bars(symbol, timeframe='day', limit=50)  # Need enough for rolling windows
        if isinstance(bars, dict) and 'error' in bars:
            return None, None, bars['error']
        df_latest = pd.DataFrame(bars)
    
    # Engineer features on the full dataset
    df_feat = engineer_features(df_latest)
    if df_feat.empty:
        return None, None, "Not enough data to compute features"
    
    # Get the last row (most recent day)
    last_row = df_feat.iloc[-1:]
    X_latest = last_row[features]
    
    # Predict probability
    prob_up = model.predict_proba(X_latest)[0][1]  # probability of class 1 (up)
    pred = model.predict(X_latest)[0]
    return prob_up, pred, None
