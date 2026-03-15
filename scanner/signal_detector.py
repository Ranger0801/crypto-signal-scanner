"""
signal_detector.py — Phase 1 + Phase 2
26 signal types across 5 categories with composite scoring.
"""
import json, logging
from datetime import datetime
from database.db import db
from database.models import Signal

log = logging.getLogger(__name__)

SCORE_MAP = {
    "MACD Bullish": 2, "MACD Bearish": 2,
    "EMA Crossover Bullish": 2, "EMA Crossover Bearish": 2,
    "EMA200 Bullish Trend": 1, "EMA200 Bearish Trend": 1,
    "ADX Strong Trend": 1,
    "RSI Oversold": 1, "RSI Overbought": 1,
    "RSI Bullish Divergence": 2, "RSI Bearish Divergence": 2,
    "Stochastic Bullish Cross": 1, "Stochastic Bearish Cross": 1,
    "CCI Oversold": 1, "CCI Overbought": 1,
    "Volume Spike": 1,
    "OBV Bullish": 1, "OBV Bearish": 1,
    "VWAP Bullish Cross": 1, "VWAP Bearish Cross": 1,
    "BB Lower Touch": 1, "BB Upper Touch": 1,
    "BB Squeeze Breakout Bull": 2, "BB Squeeze Breakout Bear": 2,
    "Pivot Support Bounce": 1, "Pivot Resistance Reject": 1,
    "Fib 618 Bounce": 1, "Fib 382 Bounce": 1,
}

def detect_signals(symbol: str, timeframe: str, ind: dict) -> list:
    s, i = [], ind

    # ── TREND ──────────────────────────────────────────────────────
    if i.get("macd_prev") is not None:
        if i["macd_prev"] < i["macd_sig_prev"] and i["macd_line"] > i["macd_signal"]:
            s.append(_sig("MACD Bullish", "bullish", i))
        elif i["macd_prev"] > i["macd_sig_prev"] and i["macd_line"] < i["macd_signal"]:
            s.append(_sig("MACD Bearish", "bearish", i))

    if all(i.get(k) is not None for k in ["ema20","ema50","ema20_prev","ema50_prev"]):
        if i["ema20_prev"] < i["ema50_prev"] and i["ema20"] > i["ema50"]:
            s.append(_sig("EMA Crossover Bullish", "bullish", i))
        elif i["ema20_prev"] > i["ema50_prev"] and i["ema20"] < i["ema50"]:
            s.append(_sig("EMA Crossover Bearish", "bearish", i))

    if i.get("ema200") and i.get("close"):
        if i["close"] > i["ema200"]: s.append(_sig("EMA200 Bullish Trend", "bullish", i))
        else:                         s.append(_sig("EMA200 Bearish Trend", "bearish", i))

    if i.get("adx") and i["adx"] > 25:
        d = "bullish" if i.get("adx_dmp", 0) > i.get("adx_dmn", 0) else "bearish"
        s.append(_sig("ADX Strong Trend", d, i))

    # ── MOMENTUM ───────────────────────────────────────────────────
    if i.get("rsi") is not None:
        if i["rsi"] < 30:   s.append(_sig("RSI Oversold",   "bullish", i))
        elif i["rsi"] > 70: s.append(_sig("RSI Overbought", "bearish", i))

    if i.get("rsi") and i.get("rsi_prev"):
        if i["close"] < i.get("close",0) and i["rsi"] > i["rsi_prev"] and i["rsi"] < 50:
            s.append(_sig("RSI Bullish Divergence", "bullish", i))
        elif i["close"] > i.get("close",0) and i["rsi"] < i["rsi_prev"] and i["rsi"] > 50:
            s.append(_sig("RSI Bearish Divergence", "bearish", i))

    if all(i.get(k) is not None for k in ["stoch_k","stoch_d","stoch_k_prev","stoch_d_prev"]):
        if i["stoch_k_prev"] < i["stoch_d_prev"] and i["stoch_k"] > i["stoch_d"] and i["stoch_k"] < 30:
            s.append(_sig("Stochastic Bullish Cross", "bullish", i))
        elif i["stoch_k_prev"] > i["stoch_d_prev"] and i["stoch_k"] < i["stoch_d"] and i["stoch_k"] > 70:
            s.append(_sig("Stochastic Bearish Cross", "bearish", i))

    if i.get("cci") is not None:
        if i["cci"] < -100: s.append(_sig("CCI Oversold",   "bullish", i))
        elif i["cci"] > 100: s.append(_sig("CCI Overbought","bearish", i))

    # ── VOLUME ─────────────────────────────────────────────────────
    if i.get("volume_ratio") and i["volume_ratio"] >= 2.0:
        s.append(_sig("Volume Spike", "neutral", i))

    if i.get("obv") and i.get("obv_prev"):
        if i["obv"] > i["obv_prev"]: s.append(_sig("OBV Bullish", "bullish", i))
        else:                         s.append(_sig("OBV Bearish", "bearish", i))

    if i.get("vwap") and i.get("close") and i.get("atr"):
        margin = i["vwap"] * 0.002
        if i["close"] > i["vwap"] + margin:   s.append(_sig("VWAP Bullish Cross", "bullish", i))
        elif i["close"] < i["vwap"] - margin: s.append(_sig("VWAP Bearish Cross", "bearish", i))

    # ── VOLATILITY ─────────────────────────────────────────────────
    if i.get("bb_pct") is not None:
        if i["bb_pct"] <= 0.05:   s.append(_sig("BB Lower Touch", "bullish", i))
        elif i["bb_pct"] >= 0.95: s.append(_sig("BB Upper Touch", "bearish", i))

    if i.get("bb_squeeze") and i.get("macd_hist") is not None:
        if i["macd_hist"] > 0:   s.append(_sig("BB Squeeze Breakout Bull", "bullish", i))
        elif i["macd_hist"] < 0: s.append(_sig("BB Squeeze Breakout Bear", "bearish", i))

    # ── LEVELS ─────────────────────────────────────────────────────
    close, atr = i.get("close", 0), i.get("atr") or 0
    if i.get("s1")    and atr and abs(close - i["s1"])    < atr * 0.3: s.append(_sig("Pivot Support Bounce",    "bullish", i))
    if i.get("r1")    and atr and abs(close - i["r1"])    < atr * 0.3: s.append(_sig("Pivot Resistance Reject", "bearish", i))
    if i.get("fib_618") and atr and abs(close - i["fib_618"]) < atr * 0.3: s.append(_sig("Fib 618 Bounce", "bullish", i))
    if i.get("fib_382") and atr and abs(close - i["fib_382"]) < atr * 0.3: s.append(_sig("Fib 382 Bounce", "bullish", i))

    return s


def compute_composite_score(signals: list) -> int:
    return sum(SCORE_MAP.get(s["signal_type"], 1) for s in signals)


def build_summary(signals: list, score: int, ind: dict) -> dict:
    bullish = [s["signal_type"] for s in signals if s["direction"] == "bullish"]
    bearish = [s["signal_type"] for s in signals if s["direction"] == "bearish"]
    overall = "bullish" if len(bullish) > len(bearish) else \
              "bearish" if len(bearish) > len(bullish) else "neutral"
    return {"score": score, "overall": overall, "bullish": bullish,
            "bearish": bearish, "atr": ind.get("atr"),
            "stop_distance": ind.get("stop_distance"), "close": ind.get("close")}


def save_signals(app, symbol, timeframe, signals, score,
                 confidence=None, ai_explanation=None):
    """Save detected signals to DB — includes Phase 3 fields."""
    if not signals:
        return
    with app.app_context():
        for sig in signals:
            db.session.add(Signal(
                coin_symbol    = symbol,
                signal_type    = sig["signal_type"],
                direction      = sig["direction"],
                timeframe      = timeframe,
                score          = score,
                confidence     = confidence,
                ai_explanation = ai_explanation,
                details        = json.dumps(sig["details"]),
                timestamp      = datetime.utcnow(),
            ))
        db.session.commit()
        log.info(f"[{symbol} {timeframe}] {len(signals)} signals — score {score}"
                 + (f" — confidence {confidence}%" if confidence else ""))


def _sig(signal_type, direction, i):
    return {"signal_type": signal_type, "direction": direction, "details": {
        "close": i.get("close"), "rsi": i.get("rsi"),
        "macd": i.get("macd_line"), "macd_signal": i.get("macd_signal"),
        "macd_hist": i.get("macd_hist"),
        "ema20": i.get("ema20"), "ema50": i.get("ema50"), "ema200": i.get("ema200"),
        "adx": i.get("adx"), "stoch_k": i.get("stoch_k"), "cci": i.get("cci"),
        "vwap": i.get("vwap"), "bb_pct": i.get("bb_pct"),
        "bb_squeeze": i.get("bb_squeeze"), "volume_ratio": i.get("volume_ratio"),
        "atr": i.get("atr"), "stop_distance": i.get("stop_distance"),
        "pivot": i.get("pivot"), "r1": i.get("r1"), "s1": i.get("s1"),
        "fib_618": i.get("fib_618"),
    }}
