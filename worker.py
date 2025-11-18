# worker.py
import time
import sqlite3
from typing import List
from data_fetcher import get_latest_price_yf

DB_PATH = "prices.db"
SYMBOLS: List[str] = ["AAPL", "MSFT", "TSLA"]
POLL_INTERVAL_SECONDS = 15  # you can change to 10, 30, etc.


def init_db():
    """Create the quotes table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            ts INTEGER NOT NULL,
            price REAL NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()
    print("[worker] DB initialized (table 'quotes' ready).")


def save_quote(symbol: str, price: float):
    """Insert one row into quotes table."""
    ts = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO quotes (symbol, ts, price) VALUES (?, ?, ?);",
        (symbol.upper(), ts, float(price)),
    )
    conn.commit()
    conn.close()
    print(f"[worker] Saved {symbol.upper()} {price} at {time.strftime('%X')}")


def run_loop():
    init_db()
    print(f"[worker] Tracking symbols: {SYMBOLS}, interval={POLL_INTERVAL_SECONDS}s")
    try:
        while True:
            for sym in SYMBOLS:
                price = get_latest_price_yf(sym)
                if price is None:
                    print(f"[worker] No price for {sym} at {time.strftime('%X')}")
                else:
                    save_quote(sym, price)
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n[worker] Stopped by user.")


if __name__ == "__main__":
    run_loop()
