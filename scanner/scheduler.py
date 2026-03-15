"""
scheduler.py — Phase 1 + 2 + 3
Phase 1+2: fetch -> indicators -> signals -> save to DB
Phase 3:   ML confidence score + Claude AI explanation + Telegram alert
           Weekly: retrain ML model + run backtest
"""
import json, logging, os, threading, time
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from scanner.fetch_data import fetch_ohlcv, fetch_market_data
from scanner.indicators import calculate_indicators
from scanner.signal_detector import detect_signals, compute_composite_score, save_signals
from scanner.ai_explainer import explain_signal
from scanner.ml_model import predict_win_probability, train_model
from scanner.telegram_alerts import send_signal_alert

log = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone="UTC")

TELEGRAM_THRESHOLD = 7   # send alert at score >= 7
AI_THRESHOLD       = 10  # generate AI explanation at score >= 10


def run_scan(app):
    log.info("🔍 Scan started...")
    f = os.path.join(os.path.dirname(__file__), "..", "data", "coin_list.json")
    coins = json.load(open(f))["coins"]

    market_data = fetch_market_data([c["coingecko_id"] for c in coins])
    _update_prices(app, coins, market_data)

    for coin in coins:
        sym = coin["symbol"]
        for tf in Config.TIMEFRAMES:
            df  = fetch_ohlcv(sym, interval=tf, limit=210)
            ind = calculate_indicators(df)
            if ind is None:
                continue

            signals = detect_signals(sym, tf, ind)
            if not signals:
                continue

            score = compute_composite_score(signals)

            # ── Phase 3: ML confidence score ───────────────
            confidence = predict_win_probability(ind, score)

            # ── Phase 3: AI explanation (score >= 10 only) ─
            ai_text = None
            if score >= AI_THRESHOLD:
                ai_text = explain_signal(sym, tf, signals, score, ind)

            # ── Phase 1+2: save to DB ──────────────────────
            save_signals(app, sym, tf, signals, score, confidence, ai_text)

            # ── Phase 3: Telegram alert (score >= 7) ───────
            if score >= TELEGRAM_THRESHOLD:
                send_signal_alert(sym, tf, signals, score, ind, ai_text, confidence)

    log.info("✅ Scan complete.")


def run_weekly_tasks(app):
    """Retrain ML model and run backtest — called once per week."""
    log.info("📅 Running weekly tasks...")
    train_model(app)
    from scanner.backtester import run_backtest
    run_backtest(app)
    log.info("📅 Weekly tasks done.")


def _update_prices(app, coins, market_data):
    from database.db import db
    from database.models import Coin
    with app.app_context():
        for coin in coins:
            data = market_data.get(coin["coingecko_id"])
            if not data:
                continue
            r = Coin.query.filter_by(symbol=coin["symbol"]).first()
            if r:
                r.price      = data.get("price")
                r.volume_24h = data.get("volume_24h")
                r.change_24h = data.get("change_24h")
                r.market_cap = data.get("market_cap")
        db.session.commit()


def start_scheduler(app):
    # Main scan every N minutes
    _scheduler.add_job(run_scan, args=[app], trigger="interval",
        minutes=Config.SCAN_INTERVAL_MINUTES, id="scan", replace_existing=True)

    # Weekly ML retrain + backtest (every Sunday at 2am UTC)
    _scheduler.add_job(run_weekly_tasks, args=[app], trigger="cron",
        day_of_week="sun", hour=2, minute=0, id="weekly", replace_existing=True)

    _scheduler.start()
    log.info(f"⏰ Scheduler running every {Config.SCAN_INTERVAL_MINUTES} min.")
    threading.Thread(target=run_scan, args=[app], daemon=True).start()


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
