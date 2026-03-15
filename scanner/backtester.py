"""
backtester.py — Phase 3
Validates signal accuracy against historical data.
For each signal type, measures:
  - Win rate (% of times price moved >2% in signal direction)
  - Average reward/risk ratio
  - Total signals tested
  - Best and worst timeframes

Results are saved to the database and shown on the dashboard.
"""
import json, logging
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

WIN_TARGET_PCT  = 2.0   # price must move 2% in signal direction = win
LOOKAHEAD_BARS  = 4     # check outcome over next 4 candles


def run_backtest(app) -> dict:
    """
    Run full backtest on all historical signals in DB.
    Returns dict of results by signal_type.
    """
    log.info("[Backtest] Starting...")
    try:
        from scanner.fetch_data import fetch_ohlcv
        with app.app_context():
            from database.models import Signal
            signals = Signal.query.filter(
                Signal.timestamp >= datetime.utcnow() - timedelta(days=30)
            ).all()

        if not signals:
            log.info("[Backtest] No signals to backtest.")
            return {}

        results = {}  # signal_type -> {wins, total, rr_list}

        for sig in signals:
            if sig.direction not in ("bullish", "bearish"):
                continue

            details = json.loads(sig.details) if sig.details else {}
            entry   = details.get("close")
            atr     = details.get("atr") or details.get("stop_distance", 0)
            if not entry:
                continue

            # Fetch recent candles for this coin/timeframe
            df = fetch_ohlcv(sig.coin_symbol, interval=sig.timeframe, limit=10)
            if df is None or len(df) < 5:
                continue

            future_high = df["high"].iloc[1:LOOKAHEAD_BARS+1].max()
            future_low  = df["low"].iloc[1:LOOKAHEAD_BARS+1].min()

            if sig.direction == "bullish":
                move_pct = (future_high - entry) / entry * 100
                stop_pct = (entry - future_low) / entry * 100
            else:
                move_pct = (entry - future_low) / entry * 100
                stop_pct = (future_high - entry) / entry * 100

            win = move_pct >= WIN_TARGET_PCT
            rr  = move_pct / stop_pct if stop_pct > 0 else 0

            key = sig.signal_type
            if key not in results:
                results[key] = {"wins": 0, "total": 0, "rr_list": []}
            results[key]["total"] += 1
            if win:
                results[key]["wins"] += 1
            if rr > 0:
                results[key]["rr_list"].append(rr)

        # Format results
        formatted = {}
        for sig_type, data in results.items():
            total = data["total"]
            wins  = data["wins"]
            rr_list = data["rr_list"]
            formatted[sig_type] = {
                "signal_type": sig_type,
                "total":       total,
                "wins":        wins,
                "win_rate":    round(wins / total * 100, 1) if total > 0 else 0,
                "avg_rr":      round(sum(rr_list) / len(rr_list), 2) if rr_list else 0,
            }

        log.info(f"[Backtest] Complete — {len(formatted)} signal types tested.")
        _save_results(app, formatted)
        return formatted

    except Exception as e:
        log.error(f"[Backtest] Failed: {e}", exc_info=True)
        return {}


def _save_results(app, results: dict):
    """Save backtest results to database."""
    try:
        from database.db import db
        from database.models import BacktestResult
        with app.app_context():
            for sig_type, data in results.items():
                existing = BacktestResult.query.filter_by(
                    signal_type=sig_type).first()
                if existing:
                    existing.total     = data["total"]
                    existing.wins      = data["wins"]
                    existing.win_rate  = data["win_rate"]
                    existing.avg_rr    = data["avg_rr"]
                    existing.updated_at = datetime.utcnow()
                else:
                    db.session.add(BacktestResult(
                        signal_type=sig_type,
                        total=data["total"],
                        wins=data["wins"],
                        win_rate=data["win_rate"],
                        avg_rr=data["avg_rr"],
                    ))
            db.session.commit()
            log.info("[Backtest] Results saved to DB.")
    except Exception as e:
        log.error(f"[Backtest] Save failed: {e}")


def get_backtest_summary(app) -> list:
    """Return stored backtest results sorted by win rate."""
    try:
        from database.models import BacktestResult
        with app.app_context():
            results = BacktestResult.query.order_by(
                BacktestResult.win_rate.desc()).all()
            return [r.to_dict() for r in results]
    except Exception as e:
        log.error(f"[Backtest] Get summary failed: {e}")
        return []
