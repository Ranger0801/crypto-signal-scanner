import pandas as pd, numpy as np
from config import MIN_VOLUME_SPIKE

def macd(df, fast=12, slow=26, signal=9):
    df = df.copy()
    ef = df["close"].ewm(span=fast, adjust=False).mean()
    es = df["close"].ewm(span=slow, adjust=False).mean()
    ml = ef - es
    sl = ml.ewm(span=signal, adjust=False).mean()
    df["macd_line"], df["macd_signal"], df["macd_hist"] = ml, sl, ml-sl
    return df

def ema(df, periods=[20,50,200]):
    df = df.copy()
    for p in periods:
        df[f"ema_{p}"] = df["close"].ewm(span=p, adjust=False).mean()
    return df

def rsi(df, period=14):
    df = df.copy()
    d = df["close"].diff()
    g = d.clip(lower=0).ewm(com=period-1, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(com=period-1, adjust=False).mean()
    df["rsi"] = 100 - 100/(1 + g/l.replace(0, np.nan))
    return df

def volume_spike(df, window=20, threshold=None):
    threshold = threshold or MIN_VOLUME_SPIKE
    df = df.copy()
    df["vol_avg"]   = df["volume"].rolling(window).mean()
    df["vol_ratio"] = df["volume"] / df["vol_avg"].replace(0, np.nan)
    df["vol_spike"] = df["vol_ratio"] >= threshold
    return df

def support_resistance(df, window=20):
    df = df.copy()
    df["support"]    = df["low"].rolling(window).min()
    df["resistance"] = df["high"].rolling(window).max()
    return df

def apply_all(df):
    for fn in [macd, ema, rsi, volume_spike, support_resistance]:
        df = fn(df)
    return df
