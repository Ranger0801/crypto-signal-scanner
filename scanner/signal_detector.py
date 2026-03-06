import json
import pandas as pd
from scanner.fetch_data import get_ohlc
from scanner.indicators import apply_all
from config import DEFAULT_TF

SCORES = {
    "MACD Bullish Crossover": 2, "MACD Bearish Crossover": 2,
    "EMA Golden Cross": 2,       "EMA Death Cross": 2,
    "RSI Oversold": 1,           "RSI Overbought": 1,
    "Volume Spike": 1,           "Near Support": 1, "Near Resistance": 1,
}
DIRECTION = {
    "MACD Bullish Crossover":"bullish","EMA Golden Cross":"bullish",
    "RSI Oversold":"bullish","Near Support":"bullish",
    "MACD Bearish Crossover":"bearish","EMA Death Cross":"bearish",
    "RSI Overbought":"bearish","Near Resistance":"bearish",
    "Volume Spike":"neutral",
}

def _macd(df):
    p,c = df.iloc[-2], df.iloc[-1]
    if p["macd_line"] < p["macd_signal"] and c["macd_line"] > c["macd_signal"]:
        return ["MACD Bullish Crossover"]
    if p["macd_line"] > p["macd_signal"] and c["macd_line"] < c["macd_signal"]:
        return ["MACD Bearish Crossover"]
    return []

def _ema_cross(df):
    if "ema_50" not in df.columns: return []
    p,c = df.iloc[-2], df.iloc[-1]
    if p["ema_50"] < p["ema_200"] and c["ema_50"] > c["ema_200"]: return ["EMA Golden Cross"]
    if p["ema_50"] > p["ema_200"] and c["ema_50"] < c["ema_200"]: return ["EMA Death Cross"]
    return []

def _rsi(df):
    v = df.iloc[-1]["rsi"]
    if pd.notna(v):
        if v <= 30: return ["RSI Oversold"]
        if v >= 70: return ["RSI Overbought"]
    return []

def _volume(df):
    return ["Volume Spike"] if df.iloc[-1].get("vol_spike", False) else []

def _sr(df, tol=0.015):
    sigs, last = [], df.iloc[-1]
    p = last["close"]
    if pd.notna(last.get("support"))    and abs(p-last["support"])/last["support"] <= tol:   sigs.append("Near Support")
    if pd.notna(last.get("resistance")) and abs(p-last["resistance"])/last["resistance"] <= tol: sigs.append("Near Resistance")
    return sigs

def scan_symbol(symbol, timeframe=DEFAULT_TF):
    try:
        df = apply_all(get_ohlc(symbol, timeframe, 250))
        detected = _macd(df) + _ema_cross(df) + _rsi(df) + _volume(df) + _sr(df)
        if not detected: return None
        score    = sum(SCORES.get(s,1) for s in detected)
        primary  = max(detected, key=lambda s: SCORES.get(s,1))
        bullish  = sum(1 for s in detected if DIRECTION.get(s)=="bullish")
        bearish  = sum(1 for s in detected if DIRECTION.get(s)=="bearish")
        direction= "bullish" if bullish>bearish else ("bearish" if bearish>bullish else "neutral")
        return {"symbol":symbol,"signal_type":primary,"direction":direction,
                "timeframe":timeframe,"score":score,
                "indicators":json.dumps(detected),"price":float(df.iloc[-1]["close"])}
    except Exception as e:
        print(f"[scan] {symbol} error: {e}")
        return None

def scan_all(symbols, timeframe=DEFAULT_TF):
    results = [r for s in symbols if (r := scan_symbol(s, timeframe))]
    return sorted(results, key=lambda x: x["score"], reverse=True)
