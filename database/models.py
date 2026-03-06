from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
Base = declarative_base()

class Coin(Base):
    __tablename__ = "coins"
    id         = Column(Integer, primary_key=True)
    symbol     = Column(String(20), unique=True, nullable=False, index=True)
    price      = Column(Float, default=0.0)
    volume_24h = Column(Float, default=0.0)
    change_24h = Column(Float, default=0.0)
    high_24h   = Column(Float, default=0.0)
    low_24h    = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def to_dict(self):
        return {"symbol":self.symbol,"price":self.price,"volume_24h":self.volume_24h,
                "change_24h":self.change_24h,"high_24h":self.high_24h,"low_24h":self.low_24h,
                "updated_at":self.updated_at.isoformat() if self.updated_at else None}

class Signal(Base):
    __tablename__ = "signals"
    id          = Column(Integer, primary_key=True)
    symbol      = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(60), nullable=False)
    direction   = Column(String(10), default="neutral")
    timeframe   = Column(String(10), nullable=False)
    score       = Column(Integer, default=0)
    indicators  = Column(Text, default="[]")
    price       = Column(Float, default=0.0)
    created_at  = Column(DateTime, default=datetime.utcnow, index=True)
    def to_dict(self):
        import json
        return {"id":self.id,"symbol":self.symbol,"signal_type":self.signal_type,
                "direction":self.direction,"timeframe":self.timeframe,"score":self.score,
                "indicators":json.loads(self.indicators or "[]"),"price":self.price,
                "created_at":self.created_at.isoformat() if self.created_at else None}
