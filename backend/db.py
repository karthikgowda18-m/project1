# backend/db.py
from sqlalchemy import Column, Integer, String, Float, BigInteger, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

DATABASE_URL = "sqlite:///../prices.db"  # relative to backend folder

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    ts = Column(BigInteger, index=True)  # unix epoch seconds
    price = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)
