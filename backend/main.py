# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import time

from .db import SessionLocal, init_db, Quote
from .schemas import QuoteOut, HistoryOut, PricePoint

init_db()

app = FastAPI(title="Live Stock Tracker API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok", "time": int(time.time())}

@app.get("/latest/{symbol}", response_model=QuoteOut)
def latest(symbol: str, db: Session = Depends(get_db)):
    q = db.query(Quote).filter(Quote.symbol == symbol.upper()).order_by(Quote.ts.desc()).first()
    if not q:
        raise HTTPException(status_code=404, detail="No data for this symbol yet")
    return q

@app.get("/history/{symbol}", response_model=HistoryOut)
def history(symbol: str, limit: int = Query(500, ge=1, le=10000), db: Session = Depends(get_db)):
    rows = db.query(Quote).filter(Quote.symbol == symbol.upper()).order_by(Quote.ts.desc()).limit(limit).all()
    points = [PricePoint(ts=r.ts, price=r.price) for r in reversed(rows)]
    return HistoryOut(symbol=symbol.upper(), points=points)

@app.get("/symbols", response_model=List[str])
def list_symbols(db: Session = Depends(get_db)):
    rows = db.query(Quote.symbol).distinct().all()
    return [r[0] for r in rows]
