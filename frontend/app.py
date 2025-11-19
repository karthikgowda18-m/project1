import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
import requests

# ---------- CRYPTO SHORTCUTS ----------
CRYPTO_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": "BNB-USD",
    "XRP": "XRP-USD",
    "DOGE": "DOGE-USD",
    "ADA": "ADA-USD",
    "SOL": "SOL-USD",
    "DOT": "DOT-USD",
    "MATIC": "MATIC-USD",
}

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Live Market Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- GLOBAL STYLE ----------
st.markdown(
    """
    <style>
    .main { background-color: #050609; color: #f9fafb; }
    [data-testid="stSidebar"] { background-color: #050609; border-right: 1px solid #1f2937; }
    .card {
        background: #111827;
        border-radius: 16px;
        padding: 16px 20px;
        border: 1px solid #1f2937;
        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
    }
    .card-title { font-size: 0.85rem; color: #9ca3af; margin-bottom: 4px; }
    .card-value { font-size: 1.4rem; font-weight: 600; color: #f9fafb; }
    .card-sub { font-size: 0.8rem; color: #6b7280; }
    .positive { color: #22c55e; }
    .negative { color: #f97373; }
    .section-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.4rem; color: #e5e7eb; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HELPERS ----------
def flatten_df(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns like ('Close','AAPL') -> 'Close'."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df


def detect_asset_type(sym: str) -> str:
    if sym.endswith("=X"):
        return "Currency Pair"
    elif "-" in sym:
        return "Cryptocurrency"
    return "Stock / ETF"


# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 💹 Live Tracker")
    refresh_sec = st.slider("Auto-refresh (seconds)", 5, 60, 15)
    interval = st.selectbox("Interval", ["1m", "5m", "15m", "1h", "1d"], index=1)
    st.markdown("---")
    st.markdown("💡 Examples:")
    st.markdown("- AAPL, TSLA (Stocks)")
    st.markdown("- BTC or BTC-USD (Crypto)")
    st.markdown("- USDINR=X (Currency pair)")
    st.markdown("- RELIANCE.NS (NSE India)")

# optional auto-refresh
try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=refresh_sec * 1000, key="auto_refresh")
except ImportError:
    pass

# ---------- HEADER ----------
st.markdown("## 📊 Live Market Dashboard")

# ---------- SYMBOL INPUT ----------
symbol_input = st.text_input(
    "Search symbol:",
    value="AAPL",
    placeholder="Try: BTC, BTC-USD, USDINR=X, RELIANCE.NS, TSLA",
)
symbol_input = symbol_input.strip().upper()
symbol = CRYPTO_MAP.get(symbol_input, symbol_input)

# ---------- VALIDATE SYMBOL ----------
test_data = yf.Ticker(symbol).history(period="1d")
if test_data.empty:
    st.error(
        f"No data found for **'{symbol_input}'**.\n\n"
        "Try valid formats like **BTC-USD**, **TSLA**, **USDINR=X**, **RELIANCE.NS**."
    )
    st.stop()

asset_type = detect_asset_type(symbol)

# ---------- DATA FETCH ----------
@st.cache_data(ttl=30)
def load_data(sym: str, interval: str):
    df = yf.download(sym, period="5d", interval=interval, progress=False)
    if df.empty:
        df = yf.download(sym, period="1mo", interval="1d", progress=False)
    if df.empty:
        return None
    return flatten_df(df.reset_index())


hist_df = load_data(symbol, interval)
if hist_df is None:
    st.error("Failed to download price data from Yahoo Finance.")
    st.stop()

# ---------- BASIC METRICS ----------
last_close = float(hist_df["Close"].iloc[-1])
prev_close = float(hist_df["Close"].iloc[-2]) if len(hist_df) > 1 else last_close
day_high = float(hist_df["High"].iloc[-1])
day_low = float(hist_df["Low"].iloc[-1])
volume = int(hist_df["Volume"].iloc[-1]) if "Volume" in hist_df else None

change = last_close - prev_close
change_pct = (change / prev_close * 100) if prev_close else 0.0
change_class = "positive" if change >= 0 else "negative"

fmt = lambda v: f"{v:.2f}" if v is not None else "N/A"

# ---------- METRIC CARDS ----------
st.markdown("### 📌 Key Metrics")
c1, c2, c3, c4 = st.columns(4)

c1.markdown(
    f"""
    <div class="card">
        <div class="card-title">{asset_type} — {symbol}</div>
        <div class="card-value">{fmt(last_close)}</div>
        <div class="card-sub">Prev Close: {fmt(prev_close)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

c2.markdown(
    f"""
    <div class="card">
        <div class="card-title">Day Change</div>
        <div class="card-value {change_class}">{fmt(last_close)}</div>
        <div class="card-sub {change_class}">{change:+.2f} ({change_pct:+.2f}%)</div>
    </div>
    """,
    unsafe_allow_html=True,
)

c3.markdown(
    f"""
    <div class="card">
        <div class="card-title">Day Range</div>
        <div class="card-value">{fmt(day_low)} – {fmt(day_high)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

c4.markdown(
    f"""
    <div class="card">
        <div class="card-title">Volume</div>
        <div class="card-value">{volume if volume is not None else "N/A"}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- PRICE CHART ----------
st.markdown("### 📈 Price Chart")

chart_df = hist_df.copy()
time_col = chart_df.columns[0]
chart_df[time_col] = chart_df[time_col].astype(str)

fig = px.line(
    chart_df,
    x=time_col,
    y="Close",
    labels={"Close": f"{symbol} Price", time_col: "Time"},
)
fig.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

# ---------- RECENT DATA TABLE ----------
st.markdown("### 🧾 Recent Price History")
st.dataframe(
    chart_df[[time_col, "Close"]].tail(20),
    use_container_width=True,
)

# ---------- WEATHER SECTION ----------
st.markdown("---")
st.markdown("## 🌤 Live Local Weather")

API_KEY = "89e49d4efad746c0d9609568c4002014"

# 1) Try to detect city from IP
auto_city = ""
auto_country = ""
try:
    ip_info = requests.get("https://ipinfo.io", timeout=5).json()
    auto_city = ip_info.get("city", "") or ""
    auto_country = ip_info.get("country", "") or ""
except Exception:
    auto_city = ""
    auto_country = ""

# 2) Let user override / type any city
col_city, col_unit = st.columns([3, 1])
with col_city:
    city_input = st.text_input(
        "Enter city name (or keep detected):",
        value=auto_city,
        placeholder="Example: Chennai, London, Dubai",
    )
with col_unit:
    unit = st.selectbox("Units", ["metric", "imperial"], index=0)

city_to_use = city_input.strip()

if city_to_use:
    units_label_temp = "°C" if unit == "metric" else "°F"
    units_label_wind = "m/s" if unit == "metric" else "mph"

    weather_url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={city_to_use}&appid={API_KEY}&units={unit}"
    )

    try:
        resp = requests.get(weather_url, timeout=8)
        data = resp.json()

        if str(data.get("cod")) != "200":
            msg = data.get("message", "Unknown error")
            st.warning(f"Unable to fetch weather for **{city_to_use}**: {msg}")
        else:
            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"].title()
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            st.markdown(
                f"""
                <div class="card">
                    <div class="card-title">📍 Location: {city_to_use}</div>
                    <div class="card-value">{temp:.1f}{units_label_temp}</div>
                    <div class="card-sub">{condition}</div>
                    <div class="card-sub">
                        💧 Humidity: {humidity}% &nbsp;|&nbsp;
                        🌬 Wind: {wind} {units_label_wind}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    except Exception:
        st.error("Error retrieving weather data. Please check your internet connection.")
else:
    st.info("Enter a city name above to view weather conditions.")

st.markdown("---")
st.info("💡 Dashboard supports Stocks, Crypto, Currencies, and Weather — all in one place.")
