"""
ml_model.py — Phase 3
XGBoost model that predicts win probability for each detected signal.

How it works:
  1. Collect historical signals from the database
  2. For each signal, check if price moved >2% in signal direction within 4 hours
  3. That becomes the training label (win=1, loss=0)
  4. Train XGBoost on indicator values as features
  5. For new signals, predict win probability (0-100%)

The model is retrained weekly automatically.
On first run with no data, it returns None (no prediction yet).
"""
import os, logging, joblib
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ml_model.joblib")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ml_scaler.joblib")

# Features used for prediction — must match training
FEATURES = [
    "rsi", "adx", "macd_hist", "ema_spread_pct",
    "volume_ratio", "bb_pct", "atr_pct", "stoch_k", "cci_norm",
    "score",
]

# Minimum signals needed before we train
MIN_TRAINING_SAMPLES = 100


def predict_win_probability(ind: dict, score: int) -> float | None:
    """
    Predict the probability (0-100%) that this signal will be profitable.
    Returns None if model not trained yet.
    """
    if not os.path.exists(MODEL_PATH):
        return None

    try:
        model  = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        features = _extract_features(ind, score)
        if features is None:
            return None
        X = scaler.transform([features])
        prob = model.predict_proba(X)[0][1]  # probability of class 1 (win)
        return round(float(prob) * 100, 1)
    except Exception as e:
        log.error(f"[ML] Prediction failed: {e}")
        return None


def train_model(app):
    """
    Train XGBoost on historical signal data.
    Called weekly by the scheduler.
    """
    try:
        from xgboost import XGBClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        df = _load_training_data(app)
        if df is None or len(df) < MIN_TRAINING_SAMPLES:
            log.info(f"[ML] Not enough data to train ({len(df) if df is not None else 0} samples, need {MIN_TRAINING_SAMPLES})")
            return

        X = df[FEATURES].values
        y = df["win"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y)

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test  = scaler.transform(X_test)

        model = XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            use_label_encoder=False, eval_metric="logloss",
            random_state=42
        )
        model.fit(X_train, y_train)

        acc = accuracy_score(y_test, model.predict(X_test))
        log.info(f"[ML] Model trained — accuracy: {acc:.2%} on {len(df)} samples")

        # Save model and scaler
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(model,  MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        log.info("[ML] Model saved.")

    except Exception as e:
        log.error(f"[ML] Training failed: {e}", exc_info=True)


def _load_training_data(app) -> pd.DataFrame | None:
    """
    Load historical signals from DB and label them:
    win=1 if price moved >2% in signal direction within 4 candles.
    """
    import json
    from scanner.fetch_data import fetch_ohlcv

    try:
        with app.app_context():
            from database.models import Signal
            signals = Signal.query.order_by(Signal.timestamp.desc()).limit(2000).all()

        if not signals:
            return None

        rows = []
        for sig in signals:
            details = json.loads(sig.details) if sig.details else {}
            if not details.get("close"):
                continue

            # Fetch candles after the signal to check outcome
            df = fetch_ohlcv(sig.coin_symbol, interval=sig.timeframe, limit=10)
            if df is None or len(df) < 5:
                continue

            entry_price = details["close"]
            future_high = df["high"].iloc[1:5].max()
            future_low  = df["low"].iloc[1:5].min()

            if sig.direction == "bullish":
                win = 1 if (future_high - entry_price) / entry_price > 0.02 else 0
            elif sig.direction == "bearish":
                win = 1 if (entry_price - future_low) / entry_price > 0.02 else 0
            else:
                continue

            features = _extract_features(details, sig.score)
            if features is None:
                continue

            row = dict(zip(FEATURES, features))
            row["win"] = win
            rows.append(row)

        return pd.DataFrame(rows) if rows else None

    except Exception as e:
        log.error(f"[ML] Data loading failed: {e}")
        return None


def _extract_features(ind: dict, score: int) -> list | None:
    """Extract and normalize features from indicator dict."""
    try:
        close    = ind.get("close") or 1
        ema20    = ind.get("ema20") or close
        ema50    = ind.get("ema50") or close
        atr      = ind.get("atr") or 0

        rsi         = float(ind.get("rsi") or 50)
        adx         = float(ind.get("adx") or 20)
        macd_hist   = float(ind.get("macd_hist") or 0)
        ema_spread  = (ema20 - ema50) / close * 100  # % spread
        volume_ratio= float(ind.get("volume_ratio") or 1)
        bb_pct      = float(ind.get("bb_pct") or 0.5)
        atr_pct     = atr / close * 100 if close else 0
        stoch_k     = float(ind.get("stoch_k") or 50)
        cci_norm    = float(ind.get("cci") or 0) / 200  # normalize ~-1 to 1
        score_f     = float(score)

        features = [rsi, adx, macd_hist, ema_spread, volume_ratio,
                    bb_pct, atr_pct, stoch_k, cci_norm, score_f]

        if any(np.isnan(f) or np.isinf(f) for f in features):
            return None

        return features
    except:
        return None
