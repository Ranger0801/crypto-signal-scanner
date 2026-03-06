import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import SCAN_INTERVAL_SECS, DEFAULT_TF, DEFAULT_COINS
from scanner.signal_detector import scan_all
from scanner.fetch_data import get_tickers_bulk
from database.db import SessionLocal
from database.models import Coin, Signal

def run_scan():
    print("[scheduler] Scanning market …")
    symbols = DEFAULT_COINS
    # Update coin prices
    try:
        tickers = get_tickers_bulk(symbols)
        db = SessionLocal()
        for t in tickers:
            coin = db.query(Coin).filter(Coin.symbol == t["symbol"]).first()
            if coin:
                for k,v in t.items(): setattr(coin, k, v) if k!="symbol" else None
            else:
                db.add(Coin(**t))
        db.commit()
        db.close()
    except Exception as e:
        print(f"[scheduler] Ticker error: {e}")
    # Detect signals
    signals = scan_all(symbols, DEFAULT_TF)
    db = SessionLocal()
    try:
        for sig in signals:
            db.add(Signal(**sig))
        db.commit()
        print(f"[scheduler] {len(signals)} signals saved.")
    except Exception as e:
        db.rollback(); print(f"[scheduler] DB error: {e}")
    finally:
        db.close()

def start_scheduler():
    s = BackgroundScheduler()
    s.add_job(run_scan, IntervalTrigger(seconds=SCAN_INTERVAL_SECS),
              id="scan", replace_existing=True)
    s.start()
    print(f"[scheduler] Running every {SCAN_INTERVAL_SECS}s")
    return s
