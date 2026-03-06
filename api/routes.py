from flask import Blueprint, jsonify, request
from database.db import SessionLocal
from database.models import Signal, Coin
from config import FREE_SIGNALS_LIMIT, TOP_SIGNALS_LIMIT

api_bp = Blueprint("api", __name__, url_prefix="/api")

def _premium(req):
    return req.headers.get("X-Premium-Key") == "PREMIUM_SECRET"

@api_bp.route("/signals")
def get_signals():
    db = SessionLocal()
    try:
        tf       = request.args.get("timeframe")
        minscore = int(request.args.get("min_score", 0))
        direction= request.args.get("direction")
        premium  = _premium(request)
        limit    = TOP_SIGNALS_LIMIT if premium else FREE_SIGNALS_LIMIT
        q = db.query(Signal).order_by(Signal.score.desc(), Signal.created_at.desc())
        if tf:        q = q.filter(Signal.timeframe == tf)
        if minscore:  q = q.filter(Signal.score >= minscore)
        if direction: q = q.filter(Signal.direction == direction)
        sigs = q.limit(limit).all()
        return jsonify({"ok":True,"premium":premium,"limit":limit,
                        "count":len(sigs),"data":[s.to_dict() for s in sigs]})
    finally: db.close()

@api_bp.route("/top-gainers")
def top_gainers():
    db = SessionLocal()
    try:
        coins = db.query(Coin).order_by(Coin.change_24h.desc()).limit(10).all()
        return jsonify({"ok":True,"data":[c.to_dict() for c in coins]})
    finally: db.close()

@api_bp.route("/top-losers")
def top_losers():
    db = SessionLocal()
    try:
        coins = db.query(Coin).order_by(Coin.change_24h.asc()).limit(10).all()
        return jsonify({"ok":True,"data":[c.to_dict() for c in coins]})
    finally: db.close()

@api_bp.route("/market-summary")
def market_summary():
    db = SessionLocal()
    try:
        return jsonify({"ok":True,"data":{
            "total_coins":   db.query(Coin).count(),
            "total_signals": db.query(Signal).count(),
            "gainers":       db.query(Coin).filter(Coin.change_24h > 0).count(),
            "losers":        db.query(Coin).filter(Coin.change_24h < 0).count(),
        }})
    finally: db.close()

@api_bp.route("/coin/<symbol>")
def coin_detail(symbol):
    db = SessionLocal()
    try:
        coin = db.query(Coin).filter(Coin.symbol == symbol.upper()).first()
        if not coin: return jsonify({"ok":False,"error":"Not found"}), 404
        sigs = db.query(Signal).filter(Signal.symbol==symbol.upper())\
                 .order_by(Signal.created_at.desc()).limit(20).all()
        return jsonify({"ok":True,"coin":coin.to_dict(),"signals":[s.to_dict() for s in sigs]})
    finally: db.close()
