from datetime import datetime
from database.db import db

class Coin(db.Model):
    __tablename__ = "coins"
    id         = db.Column(db.Integer, primary_key=True)
    symbol     = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name       = db.Column(db.String(100), nullable=False)
    price      = db.Column(db.Float)
    volume_24h = db.Column(db.Float)
    change_24h = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    signals    = db.relationship("Signal", backref="coin_ref", lazy="dynamic")

    def to_dict(self):
        return {"symbol": self.symbol, "name": self.name, "price": self.price,
                "volume_24h": self.volume_24h, "change_24h": self.change_24h,
                "market_cap": self.market_cap,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None}


class Signal(db.Model):
    __tablename__ = "signals"
    id             = db.Column(db.Integer, primary_key=True)
    coin_symbol    = db.Column(db.String(20), db.ForeignKey("coins.symbol"), nullable=False, index=True)
    signal_type    = db.Column(db.String(60), nullable=False)
    direction      = db.Column(db.String(10), nullable=False)
    timeframe      = db.Column(db.String(10), nullable=False)
    score          = db.Column(db.Integer, default=0)
    confidence     = db.Column(db.Float, nullable=True)      # ML win probability 0-100
    ai_explanation = db.Column(db.Text, nullable=True)       # Claude explanation
    details        = db.Column(db.Text)
    timestamp      = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {"id": self.id, "coin": self.coin_symbol,
                "signal_type": self.signal_type, "direction": self.direction,
                "timeframe": self.timeframe, "score": self.score,
                "confidence": self.confidence,
                "ai_explanation": self.ai_explanation,
                "details": self.details,
                "timestamp": self.timestamp.isoformat()}


class BacktestResult(db.Model):
    __tablename__ = "backtest_results"
    id          = db.Column(db.Integer, primary_key=True)
    signal_type = db.Column(db.String(60), unique=True, nullable=False, index=True)
    total       = db.Column(db.Integer, default=0)
    wins        = db.Column(db.Integer, default=0)
    win_rate    = db.Column(db.Float, default=0.0)
    avg_rr      = db.Column(db.Float, default=0.0)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {"signal_type": self.signal_type, "total": self.total,
                "wins": self.wins, "win_rate": self.win_rate,
                "avg_rr": self.avg_rr,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None}
