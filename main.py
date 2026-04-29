import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client

# --- 1. SETTINGS & CSS ---
st.set_page_config(page_title="Titan V5", page_icon="🦅", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    h1, h2, h3 { color: #38bdf8; font-family: 'Courier New', Courier, monospace; }
    div[data-testid="column"] { display: flex; align-items: center; }
    .stButton>button { border-radius: 4px; font-weight: bold; width: 100%; transition: all 0.2s ease; }
    .add-btn .stButton>button { background: #38bdf8; color: #0b0f19; border: none; }
    .add-btn .stButton>button:hover { background: #0ea5e9; transform: scale(1.02); }
    .auth-box { background: #1e293b; padding: 2rem; border-radius: 8px; border: 1px solid #334155; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 3. DATA DICTIONARIES ---
TICKER_NAMES = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft", "GOOGL": "Alphabet (Google)",
    "AMZN": "Amazon", "META": "Meta Platforms", "TSLA": "Tesla",
    "NVDA": "NVIDIA", "NFLX": "Netflix", "AMD": "Advanced Micro Devices",
    "INTC": "Intel", "BA": "Boeing", "DIS": "Disney", "V": "Visa",
    "JPM": "JPMorgan Chase", "WMT": "Walmart", "T": "AT&T",
    "XOM": "Exxon Mobil", "CVX": "Chevron", "PG": "Procter & Gamble",
    "KO": "Coca-Cola", "PEP": "PepsiCo", "CSCO": "Cisco",
    "PFE": "Pfizer", "MRK": "Merck", "ABBV": "AbbVie"
}
DEFAULT_TICKERS = list(TICKER_NAMES.keys())

# --- 4. SESSION STATE MANAGEMENT ---
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'home'
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = None
if 'my_tickers' not in st.session_state:
    st.session_state.my_tickers = DEFAULT_TICKERS.copy()

# --- 5. SECURE DATABASE LOGIC ---
def load_user_data():
    if st.session_state.user_email:
        response = supabase.table("secure_watchlists").select("tickers").eq("email", st.session_state.user_email).execute()
        if response.data:
            st.session_state.my_tickers = response.data[0]['tickers']
        else:
            # First time logging in? Give them the default list
            st.session_state.my_tickers = DEFAULT_TICKERS.copy()
            save_user_data()

def save_user_data():
    if st.session_state.user_email:
        supabase.table("secure_watchlists").upsert({
            "email": st.session_state.user_email, 
            "tickers": st.session_state.my_tickers
        }).execute()

# --- 6. AUTHENTICATION UI (THE LOGIN GATEWAY) ---
if st.session_state.user_email is None:
    st.title("🦅 TITAN FORENSICS")
    st.markdown("### Secure Institutional Terminal")
    st.write("Please log in or create an account to access the macro-forensics dashboard.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        auth_mode = st.radio("Select Action:", ["Login", "Sign Up"], horizontal=True)
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        
        if st.button("Execute", type="primary"):
            if auth_mode == "Sign Up":
                try:
                    # Create the user in Supabase
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Identity Confirmed. You may now log in.")
                except Exception as e:
                    st.error(f"Sign Up Error: {e}")
            
            elif auth_mode == "Login":
                try:
                    # Authenticate the user
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user_email = res.user.email
                    load_user_data() # Pull their private data
                    st.rerun() # Refresh the page to show the dashboard
                except Exception as e:
                    st.error("Access Denied. Invalid email or password.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. THE TERMINAL (ONLY VISIBLE IF LOGGED IN) ---
else:
    # Navigation Functions
    def go_to_detail(ticker):
        st.session_state.active_ticker = ticker
        st.session_state.current_view = 'detail'

    def go_to_home():
        st.session_state.active_ticker = None
        st.session_state.current_view = 'home'

    def remove_ticker(ticker):
        if ticker in st.session_state.my_tickers:
            st.session_state.my_tickers.remove(ticker)
            save_user_data()

    def add_ticker(new_ticker):
        if new_ticker and new_ticker not in st.session_state.my_tickers:
            if len(st.session_state.my_tickers) < 50:
                st.session_state.my_tickers.insert(0, new_ticker)
                save_user_data()
            else:
                st.error("Watchlist full (Max 50).")

    # Sidebar Logout
    with st.sidebar:
        st.subheader("👤 Operator Profile")
        st.success(f"Logged in as: \n{st.session_state.user_email}")
        if st.button("Terminate Session (Logout)"):
            supabase.auth.sign_out()
            st.session_state.user_email = None
            st.rerun()

    # --- HOME PAGE (INDEX VIEW) ---
    if st.session_state.current_view == 'home':
        st.title("🦅 TITAN FORENSICS | COMMAND CENTER")
        
        st.subheader("➕ Add Asset")
        c1, c2 = st.columns([4, 1])
        with c1:
            new_asset = st.text_input("Search ticker (e.g., PLTR, SPY):", label_visibility="collapsed").strip().upper()
        with c2:
            st.markdown('<div class="add-btn">', unsafe_allow_html=True)
            if st.button("Add to Index"):
                add_ticker(new_asset)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader(f"📊 Active Watchlist ({len(st.session_state.my_tickers)}/50)")
        
        for ticker in st.session_state.my_tickers:
            full_name = TICKER_NAMES.get(ticker, "Custom Asset")
            col1, col2, col3, col4 = st.columns([1, 4, 1.5, 1])
            
            with col1: st.markdown(f"**{ticker}**")
            with col2: st.markdown(f"<span style='color: #94a3b8;'>({full_name})</span>", unsafe_allow_html=True)
            with col3: st.button("🔍 View", key=f"view_{ticker}", type="primary", on_click=go_to_detail, args=(ticker,))
            with col4: st.button("❌", key=f"rem_{ticker}", on_click=remove_ticker, args=(ticker,))
            st.markdown("<hr style='margin: 0.5em 0; border: 0.5px solid #1e293b;'>", unsafe_allow_html=True)

    # --- DETAIL PAGE ---
    elif st.session_state.current_view == 'detail':
        ticker_sym = st.session_state.active_ticker
        full_name = TICKER_NAMES.get(ticker_sym, "")
        title_display = f"{ticker_sym} ({full_name})" if full_name else ticker_sym
        
        c1, c2 = st.columns([4, 1])
        with c1: st.title(f"🔍 PROFILE: {title_display}")
        with c2: st.button("⬅ RETURN", on_click=go_to_home, use_container_width=True)
        
        with st.spinner(f"Pulling real-time data for {ticker_sym}..."):
            stock = yf.Ticker(ticker_sym)
            df = stock.history(period="3mo")
            
        if not df.empty:
            latest_close = df['Close'].iloc[-1]
            latest_open = df['Open'].iloc[-1]
            latest_vol = df['Volume'].iloc[-1]
            price_delta = latest_close - df['Close'].iloc[-2]
            
            st.write("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Latest Close", f"${latest_close:,.2f}", f"${price_delta:,.2f}")
            m2.metric("Latest Open", f"${latest_open:,.2f}")
            m3.metric("Daily Trade Volume", f"{latest_vol:,.0f}")
            m4.metric("Tracking Window", "90 Days")
            st.write("---")
            
            chart_type = st.radio("Visualization Mode:", ["Standard (Line/Bar)", "Pro (Candlestick)"], horizontal=True)
            
            if chart_type == "Standard (Line/Bar)":
                col1, col2 = st.columns([2, 1])
                with col1: 
                    st.markdown("**Price Action Trend**")
                    st.line_chart(df['Close'], color="#38bdf8")
                with col2: 
                    st.markdown("**Institutional Volume**")
                    st.bar_chart(df['Volume'], color="#1e293b")
            else: 
                st.markdown("**Candlestick Price Action**")
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Could not retrieve data for {ticker_sym}. It may be delisted.")
