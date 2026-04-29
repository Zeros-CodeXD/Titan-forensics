import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import time

# --- 1. SETTINGS & CSS ---
st.set_page_config(page_title="Titan V2", page_icon="🦅", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    h1, h2, h3 { color: #38bdf8; font-family: 'Courier New', Courier, monospace; }
    .stButton>button {
        background: #1e293b; color: #38bdf8; border: 1px solid #38bdf8;
        border-radius: 6px; width: 100%; height: 60px; font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: #38bdf8; color: #0b0f19; box-shadow: 0px 0px 10px #38bdf8;
    }
    .back-btn>button { background: #ff4b4b; border: none; color: white; }
    .back-btn>button:hover { background: #ff1c1c; box-shadow: 0px 0px 10px #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE (THE APP'S BRAIN) ---
# Initialize the page router
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'home'
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = None

# Initialize the default 25 tickers
default_25 = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX", "AMD", "INTC", 
              "BA", "DIS", "V", "JPM", "WMT", "T", "XOM", "CVX", "PG", "KO", "PEP", "CSCO", "PFE", "MRK", "ABBV"]

if 'my_tickers' not in st.session_state:
    st.session_state.my_tickers = default_25

# --- 3. ROUTING FUNCTIONS ---
def go_to_detail(ticker):
    st.session_state.active_ticker = ticker
    st.session_state.current_view = 'detail'

def go_to_home():
    st.session_state.active_ticker = None
    st.session_state.current_view = 'home'

# --- 4. THE HOME PAGE ---
if st.session_state.current_view == 'home':
    st.title("🦅 TITAN FORENSICS | COMMAND CENTER")
    
    # The Searchbar & Customization Engine
    st.subheader("⚙️ Manage Watchlist (Max 50)")
    selected_tickers = st.multiselect(
        "Add or remove tickers from your terminal:", 
        options=sorted(list(set(st.session_state.my_tickers + default_25))), # Keeps defaults in the dropdown
        default=st.session_state.my_tickers,
        max_selections=50
    )
    # Save user choices to the brain
    st.session_state.my_tickers = selected_tickers
    
    st.divider()
    st.subheader("🌐 Active Equities")
    
    # Create the "Stickers" Grid (5 columns per row)
    if len(st.session_state.my_tickers) > 0:
        cols = st.columns(5)
        for i, ticker in enumerate(st.session_state.my_tickers):
            with cols[i % 5]:
                # If a sticker is clicked, run go_to_detail()
                st.button(f"📊 {ticker}", key=f"btn_{ticker}", on_click=go_to_detail, args=(ticker,))
    else:
        st.warning("Your watchlist is empty. Search for a ticker above to begin.")

# --- 5. THE DETAIL PAGE ---
elif st.session_state.current_view == 'detail':
    ticker_sym = st.session_state.active_ticker
    
    # Top Row: Title and Back Button
    c1, c2 = st.columns([4, 1])
    with c1:
        st.title(f"🔍 ASSET PROFILE: {ticker_sym}")
    with c2:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        st.button("⬅ RETURN TO HOME", on_click=go_to_home, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Fetch Data using Yahoo Finance instead of Alpha Vantage
    with st.spinner(f"Pulling real-time data for {ticker_sym}..."):
        stock = yf.Ticker(ticker_sym)
        df = stock.history(period="3mo") # Get last 3 months
        
    if not df.empty:
        # Calculate Metrics
        latest_close = df['Close'].iloc[-1]
        latest_open = df['Open'].iloc[-1]
        latest_vol = df['Volume'].iloc[-1]
        price_delta = latest_close - df['Close'].iloc[-2]
        
        # Display Metric Cards
        st.write("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Latest Close", f"${latest_close:,.2f}", f"${price_delta:,.2f}")
        m2.metric("Latest Open", f"${latest_open:,.2f}")
        m3.metric("Daily Trade Volume", f"{latest_vol:,.0f}")
        m4.metric("Tracking Window", "90 Days")
        st.write("---")
        
        # Charting System Toggle
        chart_type = st.radio("Select Visualization Mode:", ["Standard (Line/Bar)", "Pro (Candlestick)"], horizontal=True)
        
        if chart_type == "Standard (Line/Bar)":
            col1, col2 = st.columns([2, 1])
            with col1: 
                st.markdown("**Price Action Trend**")
                st.line_chart(df['Close'], color="#38bdf8")
            with col2: 
                st.markdown("**Institutional Volume**")
                st.bar_chart(df['Volume'], color="#1e293b")
                
        else: # Pro Candlestick
            st.markdown("**Candlestick Price Action**")
            fig = go.Figure(data=[go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Could not retrieve data for {ticker_sym}. It may be delisted or invalid.")
