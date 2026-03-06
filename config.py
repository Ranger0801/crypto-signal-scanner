import os
from dotenv import load_dotenv
load_dotenv()

DEBUG              = os.getenv("DEBUG", "false").lower() == "true"
SECRET_KEY         = os.getenv("SECRET_KEY", "change-me")
DATABASE_URL       = os.getenv("DATABASE_URL", "sqlite:///crypto_signals.db")
BINANCE_BASE_URL   = "https://api.binance.com"
SUPPORTED_TF       = ["5m", "15m", "1h", "4h", "1d"]
DEFAULT_TF         = "1h"
SCAN_INTERVAL_SECS = 300
TOP_SIGNALS_LIMIT  = 20
FREE_SIGNALS_LIMIT = 5
MIN_VOLUME_SPIKE   = 1.5
STRONG_SIGNAL_SCORE= 4
DEFAULT_COINS = [
    "BTCUSDT","ETHUSDT","SOLUSDT","LINKUSDT","AVAXUSDT",
    "BNBUSDT","ADAUSDT","DOTUSDT","MATICUSDT","ARBUSDT",
    "OPUSDT","LTCUSDT","UNIUSDT","AAVEUSDT","ATOMUSDT",
    "NEARUSDT","INJUSDT","SUIUSDT","TIAUSDT","JUPUSDT",
]
