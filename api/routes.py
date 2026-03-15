from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import desc
from database.db import db
from database.models import Coin, Signal, BacktestResult
from config import Config

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/signals")
def get_signals():
    tf    = request.args.get("timeframe")
    dir_  = request.args.get("direction")
    mins  = request.args.get("min_score", 0, type=int)
    limit = request.args.get("limit", 50, type=int)
    hrs   = request.args.get("hours", 24, type=int)
    cutoff = datetime.utcnow() - timedelta(hours=hrs)
    q = Signal.query.filter(Signal.timestamp >= cutoff, Signal.score >= mins)
    if tf:   q = q.filter(Signal.timeframe == tf)
    if dir_: q = q.filter(Signal.direction == dir_)
    return jsonify([s.to_dict() for s in q.order_by(desc(Signal.timestamp)).limit(limit)])

@api_bp.route("/strong_signals")
def strong_signals():
    cutoff = datetime.utcnow() - timedelta(hours=24)
    sigs = (Signal.query
        .filter(Signal.score >= Config.STRONG_SIGNAL_THRESHOLD, Signal.timestamp >= cutoff)
        .order_by(desc(Signal.score), desc(Signal.timestamp)).limit(20).all())
    return jsonify([s.to_dict() for s in sigs])

@api_bp.route("/top_gainers")
def top_gainers():
    coins = (Coin.query.filter(Coin.change_24h.isnot(None))
        .order_by(desc(Coin.change_24h)).limit(10).all())
    return jsonify([c.to_dict() for c in coins])

@api_bp.route("/top_losers")
def top_losers():
    coins = (Coin.query.filter(Coin.change_24h.isnot(None))
        .order_by(Coin.change_24h).limit(10).all())
    return jsonify([c.to_dict() for c in coins])

@api_bp.route("/coin/<symbol>")
def get_coin(symbol):
    coin = Coin.query.filter_by(symbol=symbol.upper()).first_or_404()
    cutoff = datetime.utcnow() - timedelta(hours=48)
    sigs = (Signal.query
        .filter(Signal.coin_symbol == symbol.upper(), Signal.timestamp >= cutoff)
        .order_by(desc(Signal.timestamp)).limit(20).all())
    return jsonify({"coin": coin.to_dict(), "signals": [s.to_dict() for s in sigs]})

@api_bp.route("/market_overview")
def market_overview():
    coins  = Coin.query.all()
    cutoff = datetime.utcnow() - timedelta(hours=24)
    total   = Signal.query.filter(Signal.timestamp >= cutoff).count()
    bullish = Signal.query.filter(Signal.direction == "bullish", Signal.timestamp >= cutoff).count()
    bearish = Signal.query.filter(Signal.direction == "bearish", Signal.timestamp >= cutoff).count()
    return jsonify({"coins": [c.to_dict() for c in coins],
                    "signal_counts": {"total": total, "bullish": bullish, "bearish": bearish}})

@api_bp.route("/backtest")
def backtest_results():
    """Return backtest win rates for all signal types."""
    results = BacktestResult.query.order_by(desc(BacktestResult.win_rate)).all()
    return jsonify([r.to_dict() for r in results])

@api_bp.route("/backtest/run", methods=["POST"])
def run_backtest():
    """Trigger a manual backtest run."""
    from flask import current_app
    from scanner.backtester import run_backtest as do_backtest
    import threading
    threading.Thread(target=do_backtest, args=[current_app._get_current_object()], daemon=True).start()
    return jsonify({"status": "Backtest started in background"})

@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})
