import logging, requests, pandas as pd
from config import Config

log = logging.getLogger(__name__)
BINANCE   = "https://api.binance.com"
COINGECKO = "https://api.coingecko.com/api/v3"

def fetch_ohlcv(symbol: str, interval: str = "1h", limit: int = 210) -> pd.DataFrame | None:
    try:
        r = requests.get(f"{BINANCE}/api/v3/klines",
            params={"symbol": f"{symbol}USDT", "interval": interval, "limit": limit},
            timeout=10)
        r.raise_for_status()
        df = pd.DataFrame(r.json(), columns=[
            "open_time","open","high","low","close","volume",
            "close_time","quote_vol","trades","taker_buy_base","taker_buy_quote","ignore"])
        for col in ["open","high","low","close","volume"]:
            df[col] = pd.to_numeric(df[col])
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df.set_index("open_time", inplace=True)
        return df[["open","high","low","close","volume"]]
    except Exception as e:
        log.error(f"[Binance] {symbol} {interval}: {e}")
        return None

def fetch_market_data(coin_ids: list) -> dict:
    try:
        params = {"vs_currency":"usd","ids":",".join(coin_ids),
                  "order":"market_cap_desc","per_page":50,"page":1,"sparkline":False}
        if Config.COINGECKO_API_KEY:
            params["x_cg_demo_api_key"] = Config.COINGECKO_API_KEY
        r = requests.get(f"{COINGECKO}/coins/markets", params=params, timeout=15)
        r.raise_for_status()
        return {c["id"]: {
            "symbol": c["symbol"].upper(), "name": c["name"],
            "price": c.get("current_price"), "volume_24h": c.get("total_volume"),
            "change_24h": c.get("price_change_percentage_24h"),
            "market_cap": c.get("market_cap"),
        } for c in r.json()}
    except Exception as e:
        log.error(f"[CoinGecko] {e}")
        return {}
