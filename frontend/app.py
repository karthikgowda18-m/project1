# frontend/app.py

import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Live Stock Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- CUSTOM CSS (dark UI) ----------
st.markdown(
    """
    <style>
    .main {
        background-color: #050609;
        color: #f9fafb;
    }
    [data-testid="stSidebar"] {
        background-color: #050609;
        border-right: 1px solid #1f2937;
    }
    .card {
        background: #111827;
        border-radius: 16px;
        padding: 16px 20px;
        border: 1px solid #1f2937;
        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
    }
    .card-title {
        font-size: 0.85rem;
        color: #9ca3af;
        margin-bottom: 4px;
    }
    .card-value {
        font-size: 1.4rem;
        font-weight: 600;
        color: #f9fafb;
    }
    .card-sub {
        font-size: 0.8rem;
        color: #6b7280;
    }
    .positive { color: #22c55e; }
    .negative { color: #f97373; }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
        color: #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- SIDEBAR NAV ----------
with st.sidebar:
    st.markdown("### 🪙 MetaMint (Demo)")
    st.markdown("---")
    st.markdown("**Dashboard**")
    st.markdown("• Active Stocks\n• Dividend Insights\n• Hybrid Funds")
    st.markdown("---")
    st.markdown("**Account**")
    st.markdown("• Portfolio\n• History\n• News\n• Settings")
    st.markdown("---")
    refresh_sec = st.slider(
        "Auto-refresh (seconds)",
        5,
        60,
        15,
        help="Page will auto-reload.",
    )
    interval = st.selectbox(
        "Chart interval",
        ["1m", "5m", "15m", "1h", "1d"],
        index=1,
        help="Smaller interval = more detailed intraday chart.",
    )

# auto refresh whole page
if st_autorefresh is not None:
    st_autorefresh(interval=refresh_sec * 1000, key="autorefresh")

# ---------- TOP BAR: title + SEARCH ----------
top_left, top_right = st.columns([3, 2])
with top_left:
    st.markdown("## 📈 Dashboard")

with top_right:
    symbol_input = st.text_input(
        "Search stock symbol",
        value="AAPL",
        placeholder="Example: AAPL, TSLA, RELIANCE.NS, INFY.NS",
    )

symbol = symbol_input.strip().upper()
if not symbol:
    st.warning("Please enter a stock symbol in the search bar.")
    st.stop()

# ---------- DATA FETCH HELPERS ----------

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """If df has MultiIndex columns (e.g. ('Close','AAPL')), flatten to simple names."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [str(col[0]) if isinstance(col, tuple) else str(col) for col in df.columns]
    else:
        df = df.copy()
        df.columns = [str(c) for c in df.columns]
    return df


@st.cache_data(ttl=30)
def load_intraday(sym: str, interval: str = "5m"):
    """
    Fetch intraday / recent history from yfinance.
    Cached for 30 seconds.
    """
    try:
        df = yf.download(sym, period="5d", interval=interval, progress=False)
        if df is None or df.empty:
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
        if df is None or df.empty:
            return None
        df = _flatten_columns(df)
        return df.reset_index()
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_year_range(sym: str):
    """
    Fetch 1-year data to compute 52-week high/low.
    Cached for 1 hour.
    """
    try:
        df = yf.download(sym, period="1y", interval="1d", progress=False)
        if df is None or df.empty:
            return None, None
        df = _flatten_columns(df)
        cols = df.columns
        low_col = "Low" if "Low" in cols else "Close"
        high_col = "High" if "High" in cols else "Close"
        low = float(df[low_col].min())
        high = float(df[high_col].max())
        return low, high
    except Exception:
        return None, None


hist_df = load_intraday(symbol, interval)

if hist_df is None or hist_df.empty:
    st.error(
        f"No price data received from Yahoo Finance for **{symbol}**.\n"
        "Check the symbol or your internet connection."
    )
    st.stop()

year_low_raw, year_high_raw = load_year_range(symbol)

# ---------- BASIC NUMBERS FROM HISTORY ONLY ----------

close_series = hist_df["Close"]
last_close = float(close_series.iloc[-1])
prev_close = float(close_series.iloc[-2]) if len(close_series) > 1 else None

if "Open" in hist_df.columns:
    open_price = float(hist_df["Open"].iloc[-1])
else:
    open_price = last_close

if "Low" in hist_df.columns:
    day_low = float(hist_df["Low"].iloc[-1])
else:
    day_low = last_close

if "High" in hist_df.columns:
    day_high = float(hist_df["High"].iloc[-1])
else:
    day_high = last_close

if "Volume" in hist_df.columns:
    volume = float(hist_df["Volume"].iloc[-1])
else:
    volume = None

year_low = year_low_raw if year_low_raw is not None else day_low
year_high = year_high_raw if year_high_raw is not None else day_high

if prev_close is not None and prev_close != 0:
    change = last_close - prev_close
    change_pct = (change / prev_close) * 100
else:
    change = None
    change_pct = None

change_class = "positive" if (change or 0) >= 0 else "negative"

# formatted display values
def fmt_price(v):
    return f"{v:.2f}" if v is not None else "N/A"

last_price_val = fmt_price(last_close)
prev_close_val = fmt_price(prev_close)
day_low_val = fmt_price(day_low)
day_high_val = fmt_price(day_high)
open_price_val = fmt_price(open_price)
year_low_val = fmt_price(year_low)
year_high_val = fmt_price(year_high)
volume_val = f"{int(volume):,}" if isinstance(volume, (int, float)) and volume is not None else "N/A"

if change is not None and change_pct is not None:
    change_text = f"{change:+.2f} ({change_pct:+.2f}%)"
else:
    change_text = "N/A"

# ---------- TOP METRIC CARDS ----------
row1 = st.columns(4)

with row1[0]:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">{symbol} price</div>
          <div class="card-value">{last_price_val}</div>
          <div class="card-sub">
            Prev close: {prev_close_val}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row1[1]:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Day change</div>
          <div class="card-value {change_class}">
            {last_price_val}
          </div>
          <div class="card-sub"><span class="{change_class}">{change_text}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row1[2]:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Day range</div>
          <div class="card-value">
            {day_low_val} – {day_high_val}
          </div>
          <div class="card-sub">Open: {open_price_val}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row1[3]:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">52-week range</div>
          <div class="card-value">
            {year_low_val} – {year_high_val}
          </div>
          <div class="card-sub">Volume: {volume_val}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- SECOND ROW: CHART + MINI TABLE ----------
st.markdown("")
row2_left, row2_right = st.columns([3, 2])

with row2_left:
    st.markdown('<div class="section-title">Price chart</div>', unsafe_allow_html=True)

    if "Datetime" in hist_df.columns:
        x_col = "Datetime"
    elif "Date" in hist_df.columns:
        x_col = "Date"
    else:
        x_col = hist_df.columns[0]

    fig = px.line(
        hist_df,
        x=x_col,
        y="Close",
        labels={"Close": "Price", x_col: "Time"},
    )
    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        xaxis=dict(gridcolor="#1f2937"),
        yaxis=dict(gridcolor="#1f2937"),
    )
    st.plotly_chart(fig, use_container_width=True)

with row2_right:
    st.markdown('<div class="section-title">Recent data</div>', unsafe_allow_html=True)

    if "Datetime" in hist_df.columns:
        tcol = "Datetime"
    elif "Date" in hist_df.columns:
        tcol = "Date"
    else:
        tcol = hist_df.columns[0]

    tail = hist_df[[tcol, "Close"]].copy().tail(20)
    tail.rename(columns={tcol: "Time"}, inplace=True)
    tail["Time"] = tail["Time"].astype(str)
    st.dataframe(tail, use_container_width=True, height=350)

# ---------- THIRD ROW: EXTRA SECTIONS ----------
st.markdown("")
row3 = st.columns(3)

with row3[0]:
    st.markdown('<div class="section-title">Notes</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
        <span class="card-sub">
        • Type different symbols in the search bar (AAPL, TSLA, RELIANCE.NS, INFY.NS).<br>
        • Data auto-refreshes every few seconds based on your setting.<br>
        • Values are computed from Yahoo Finance price history only.
        </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row3[1]:
    st.markdown('<div class="section-title">Watchlist idea</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
        <span class="card-sub">
        You can extend this page to support a saved watchlist,
        alerts, or multiple symbols displayed together.
        </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row3[2]:
    st.markdown('<div class="section-title">Next features</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
        <span class="card-sub">
        • Add portfolio holdings<br>
        • Add P&L calculation<br>
        • Add news feed for the selected symbol
        </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
