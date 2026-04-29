import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client

# --- 1. SETTINGS & HIGH-END CSS ---
st.set_page_config(page_title="Titan V6", page_icon="⚛", layout="wide")

st.markdown("""
    <style>
    /* Cinematic Midnight Grid Background */
    .stApp { 
        background: radial-gradient(circle at top, #0f172a 0%, #020617 100%);
        background-size: cover;
        color: #e2e8f0; 
    }
    
    /* Glowing Headers */
    h1, h2, h3 { color: #38bdf8; font-family: 'Courier New', Courier, monospace; letter-spacing: 1px;}
    
    /* Center Layout Alignment */
    div[data-testid="column"] { display: flex; align-items: center; }
    
    /* Master Button Reset */
    .stButton>button { border-radius: 4px; font-weight: bold; width: 100%; transition: all 0.3s ease; }
    
    /* The "Add to Index" High-Contrast Button */
    .add-btn .stButton>button { 
        background: #06b6d4; /* Neon Cyan */
        color: #000000; 
        border: none; 
        box-shadow: 0px 0px 10px rgba(6, 182, 212, 0.4);
    }
    .add-btn .stButton>button:hover { background: #0891b2; transform: scale(1.02); }
    
    /* The "Remove" Minimalist Button */
    .remove-btn .stButton>button {
        background: transparent;
        border: 1px solid #334155;
        color: #ef4444;
    }
    .remove-btn .stButton>button:hover {
        background: #7f1d1d;
        border-color: #ef4444;
        box-shadow: 0px 0px 8px rgba(239, 68, 68, 0.5);
    }
    
    /* Auth Box Styling */
    .auth-box { background: #0f172a; padding: 2rem; border-radius: 8px; border: 1px solid #1e293b; box-shadow: 0px 10px 30px rgba(0,0,0,0.5);}
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
    # Big customized Title
    st.markdown("<h1 style='text-align: center;'><span style='font-size: 1.2em; color: #06b6d4;'>⚛</span> TITAN FORENSICS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Secure Institutional Terminal • Authorized Personnel Only</p>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        auth_mode = st.radio("Access Level:", ["Login", "Request Access (Sign Up)"], horizontal=True)
        email = st.text_input("Corporate Email")
        password = st.text_input("Security Key (Password)", type="password")
        
        if st.button("Establish Connection", type="primary"):
            if auth_mode == "Request Access (Sign Up)":
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Credentials Registered. You may now log in.")
                except Exception as e:
                    st.error(f"Registration Error: {e}")
            
            elif auth_mode == "Login":
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user_email = res.user.email
                    load_user_data() 
                    st.rerun() 
                except Exception as e:
                    st.error("Connection Refused. Invalid credentials.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. THE TERMINAL (ONLY VISIBLE IF LOGGED IN) ---
else:
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
                st.error("Watchlist capacity reached (Max 50).")

    # Upgraded Sidebar
    with st.sidebar:
        st.markdown("### 🔒 Terminal Access Control")
        st.markdown(f"<div style='background-color: #0f172a; padding: 10px; border-radius: 5px; border-left: 3px solid #06b6d4;'><b>Active User:</b><br>{st.session_state.user_email}</div>", unsafe_allow_html=True)
        st.write("")
        if st.button("Sever Connection (Logout)"):
            supabase.auth.sign_out()
            st.session_state.user_email = None
            st.rerun()

    # --- HOME PAGE (INDEX VIEW) ---
    if st.session_state.current_view == 'home':
        st.markdown("<h1><span style='font-size: 1.2em; color: #06b6d4;'>⚛</span> TITAN COMMAND CENTER</h1>", unsafe_allow_html=True)
        
        st.subheader("➕ Target New Asset")
        c1, c2 = st.columns([4, 1])
        with c1:
            new_asset = st.text_input("Search ticker symbol (e.g., PLTR, SPY):", label_visibility="collapsed").strip().upper()
        with c2:
            st.markdown('<div class="add-btn">', unsafe_allow_html=True)
            if st.button("Add to Index"):
                add_ticker(new_asset)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader(f"📊 Live Watchlist ({len(st.session_state.my_tickers)}/50)")
        
        for ticker in st.session_state.my_tickers:
            full_name = TICKER_NAMES.get(ticker, "Custom Asset")
            col1, col2, col3, col4 = st.columns([1, 4, 1.5, 1])
            
            with col1: st.markdown(f"**{ticker}**")
            with col2: st.markdown(f"<span style='color: #94a3b8;'>({full_name})</span>", unsafe_allow_html=True)
            with col3: st.button("🔍 Analyze", key=f"view_{ticker}", type="primary", on_click=go_to_detail, args=(ticker,))
            
            # New styled remove button
            with col4: 
                st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
                st.button("🗑️", key=f"rem_{ticker}", on_click=remove_ticker, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown("<hr style='margin: 0.5em 0; border: 0.5px solid #1e293b;'>", unsafe_allow_html=True)

    # --- DETAIL PAGE ---
    elif st.session_state.current_view == 'detail':
        ticker_sym = st.session_state.active_ticker
        full_name = TICKER_NAMES.get(ticker_sym, "")
        title_display = f"{ticker_sym} ({full_name})" if full_name else ticker_sym
        
        c1, c2 = st.columns([4, 1])
        with c1: st.markdown(f"<h1><span style='font-size: 1.2em; color: #06b6d4;'>⚛</span> {title_display}</h1>", unsafe_allow_html=True)
        with c2: st.button("⬅ Return to Command", on_click=go_to_home, use_container_width=True)
        
        with st.spinner(f"Establishing secure link to exchange data for {ticker_sym}..."):
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
            
            chart_type = st.radio("Visualization Matrix:", ["Standard (Line/Bar)", "Pro (Candlestick)"], horizontal=True)
            
            if chart_type == "Standard (Line/Bar)":
                col1, col2 = st.columns([2, 1])
                with col1: 
                    st.markdown("**Price Action Trend**")
                    st.line_chart(df['Close'], color="#06b6d4")
                with col2: 
                    st.markdown("**Institutional Volume**")
                    st.bar_chart(df['Volume'], color="#1e293b")
            else: 
                st.markdown("**Candlestick Price Action**")
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Terminal Error: Asset data for {ticker_sym} could not be retrieved. Link severed.")
