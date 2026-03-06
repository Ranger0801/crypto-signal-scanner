from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base
from config import DATABASE_URL
engine = create_engine(DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}, echo=False)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
def init_db():
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables ready.")
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
