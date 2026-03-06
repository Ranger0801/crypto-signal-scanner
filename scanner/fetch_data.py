import time, requests, pandas as pd
from config import BINANCE_BASE_URL, SUPPORTED_TF

KLINES  = f"{BINANCE_BASE_URL}/api/v3/klines"
TICKER  = f"{BINANCE_BASE_URL}/api/v3/ticker/24hr"
RETRIES = 3

def _get(url, params):
    for i in range(1, RETRIES+1):
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == RETRIES: raise
            time.sleep(2)

def get_ohlc(symbol, timeframe="1h", limit=250):
    if timeframe not in SUPPORTED_TF:
        raise ValueError(f"Bad timeframe: {timeframe}")
    raw = _get(KLINES, {"symbol": symbol.upper(), "interval": timeframe, "limit": limit})
    df = pd.DataFrame(raw, columns=["open_time","open","high","low","close","volume",
        "close_time","quote_vol","trades","tbbase","tbquote","ignore"])
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c])
    df["open_time"]  = pd.to_datetime(df["open_time"],  unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    return df[["open_time","open","high","low","close","volume","close_time"]]

def get_ticker_24h(symbol):
    d = _get(TICKER, {"symbol": symbol.upper()})
    return {"symbol":d["symbol"],"price":float(d["lastPrice"]),
            "volume_24h":float(d["quoteVolume"]),"change_24h":float(d["priceChangePercent"]),
            "high_24h":float(d["highPrice"]),"low_24h":float(d["lowPrice"])}

def get_tickers_bulk(symbols):
    all_t = _get(TICKER, {})
    s_set = {s.upper() for s in symbols}
    return [{"symbol":t["symbol"],"price":float(t["lastPrice"]),
             "volume_24h":float(t["quoteVolume"]),"change_24h":float(t["priceChangePercent"]),
             "high_24h":float(t["highPrice"]),"low_24h":float(t["lowPrice"])}
            for t in all_t if t["symbol"] in s_set]
