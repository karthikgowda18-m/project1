# data_fetcher.py
import yfinance as yf
from typing import Optional

def get_latest_price_yf(symbol: str) -> Optional[float]:
    """
    Returns latest close price using yfinance. None on failure.
    """
    try:
        df = yf.download(symbol, period="1d", interval="1m", progress=False)
        if df is None or df.empty:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if hist is None or hist.empty:
                return None
            return float(hist["Close"].iloc[-1])
        return float(df["Close"].iloc[-1])
    except Exception as e:
        print(f"[data_fetcher] yfinance error for {symbol}: {e}")
        return None
