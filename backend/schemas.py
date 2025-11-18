# backend/schemas.py
from pydantic import BaseModel
from typing import List

class QuoteOut(BaseModel):
    id: int
    symbol: str
    ts: int
    price: float

    class Config:
        orm_mode = True

class PricePoint(BaseModel):
    ts: int
    price: float

class HistoryOut(BaseModel):
    symbol: str
    points: List[PricePoint]
