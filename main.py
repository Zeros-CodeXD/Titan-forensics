import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client

# --- 1. SETTINGS & HIGH-END CSS ---
st.set_page_config(page_title="Titan V7.1", page_icon="⚛", layout="wide")

st.markdown("""
    <style>
    /* Cinematic Midnight Grid Background */
    .stApp { 
        background: radial-gradient(circle at top, #0f172a 0%, #020617 100%);
        background-size: cover;
        color: #e2e8f0; 
    }
    h1, h2, h3 { color: #38bdf8; font-family: 'Courier New', Courier, monospace; letter-spacing: 1px;}
    div[data-testid="column"] { display: flex; align-items: center; }
    
    /* Terminal Button Reset */
    .stButton>button { 
        border-radius: 2px; 
        font-family: 'Courier New', Courier, monospace; 
        font-weight: bold; 
        width: 100%; 
        transition: all 0.2s ease; 
    }
    
    /* Add/Execute Buttons */
    .add-btn .stButton>button { 
        background: #06b6d4; color: #000000; border: none; 
        box-shadow: 0px 0px 8px rgba(6, 182, 212, 0.4);
    }
    .add-btn .stButton>button:hover { background: #0891b2; }
    
    /* Terminal Action Buttons */
    .action-btn .stButton>button {
        background: transparent;
        border: 1px solid #38bdf8;
        color: #38bdf8;
    }
    .action-btn .stButton>button:hover { background: rgba(56, 189, 248, 0.1); }
    
    /* Terminal Drop Buttons */
    .remove-btn .stButton>button {
        background: transparent;
        border: 1px solid #ef4444;
        color: #ef4444;
    }
    .remove-btn .stButton>button:hover { background: rgba(239, 68, 68, 0.1); }
    
    .auth-box { background: #0f172a; padding: 2rem; border-radius: 4px; border: 1px solid #1e293b; border-left: 4px solid #06b6d4;}
    </style>
""", unsafe_allow_html=True)

# --- 2. SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 3. DATA DICTIONARIES (WITH SECTORS) ---
TICKER_DATA = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology"},
    "MSFT": {"name": "Microsoft", "sector": "Technology"},
    "GOOGL": {"name": "Alphabet", "sector": "Communication"},
    "AMZN": {"name": "Amazon", "sector": "Consumer Cyclical"},
    "META": {"name": "Meta Platforms", "sector": "Communication"},
    "TSLA": {"name": "Tesla", "sector": "Consumer Cyclical"},
    "NVDA": {"name": "NVIDIA", "sector": "Technology"},
    "NFLX": {"name": "Netflix", "sector": "Communication"},
    "AMD": {"name": "Advanced Micro Devices", "sector": "Technology"},
    "INTC": {"name": "Intel", "sector": "Technology"},
    "BA": {"name": "Boeing", "sector": "Industrials"},
    "DIS": {"name": "Disney", "sector": "Communication"},
    "V": {"name": "Visa", "sector": "Financials"},
    "JPM": {"name": "JPMorgan Chase", "sector": "Financials"},
    "WMT": {"name": "Walmart", "sector": "Consumer Defensive"},
    "T": {"name": "AT&T", "sector": "Communication"},
    "XOM": {"name": "Exxon Mobil", "sector": "Energy"},
    "CVX": {"name": "Chevron", "sector": "Energy"},
    "PG": {"name": "Procter & Gamble", "sector": "Consumer Defensive"},
    "KO": {"name": "Coca-Cola", "sector": "Consumer Defensive"},
    "PEP": {"name": "PepsiCo", "sector": "Consumer Defensive"},
    "CSCO": {"name": "Cisco", "sector": "Technology"},
    "PFE": {"name": "Pfizer", "sector": "Healthcare"},
    "MRK": {"name": "Merck", "sector": "Healthcare"},
    "ABBV": {"name": "AbbVie", "sector": "Healthcare"}
}
DEFAULT_TICKERS = list(TICKER_DATA.keys())

# --- 4. SESSION STATE ---
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'current_view' not in st.session_state: st.session_state.current_view = 'home'
if 'active_ticker' not in st.session_state: st.session_state.active_ticker = None
if 'my_tickers' not in st.session_state: st.session_state.my_tickers = DEFAULT_TICKERS.copy()

# --- 5. SECURE DATABASE & CACHING LOGIC ---
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
        supabase.table("secure_watchlists").upsert({"email": st.session_state.user_email, "tickers": st.session_state.my_tickers}).execute()

# Protects IP from Yahoo Rate Limits
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_history(ticker_sym):
    try:
        stock = yf.Ticker(ticker_sym)
        return stock.history(period="3mo")
    except Exception:
        return pd.DataFrame()

# --- 6. AUTHENTICATION GATEWAY ---
if st.session_state.user_email is None:
    st.markdown("<h1 style='text-align: center;'><span style='font-size: 1.2em; color: #06b6d4;'>⚛</span> TITAN FORENSICS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Secure Institutional Terminal • Authorized Personnel Only</p><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        auth_mode = st.radio("System Access:", ["Authenticate", "Request Allocation"], horizontal=True)
        email = st.text_input("Operator ID (Email)")
        password = st.text_input("Encryption Key (Password)", type="password")
        
        if st.button("[~] INITIATE HANDSHAKE", type="primary"):
            if auth_mode == "Request Allocation":
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Credentials logged. Proceed to authenticate.")
                except Exception as e:
                    st.error(f"Registration Error: {e}")
            elif auth_mode == "Authenticate":
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user_email = res.user.email
                    load_user_data() 
                    st.rerun() 
                except Exception as e:
                    st.error("ERR_CONNECTION_REFUSED: Invalid credentials.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. THE TERMINAL ---
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
                st.error("ERR_MEMORY_FULL: Max 50 assets permitted.")

    with st.sidebar:
        st.markdown("### ⎈ ACCESS CONTROL")
        st.markdown(f"<div style='background-color: #0f172a; padding: 10px; border-radius: 2px; border-left: 2px solid #06b6d4; font-family: monospace;'><b>USER:</b><br>{st.session_state.user_email}</div><br>", unsafe_allow_html=True)
        if st.button("[x] TERMINATE SESSION"):
            supabase.auth.sign_out()
            st.session_state.user_email = None
            st.rerun()

    # --- HOME PAGE (COMMAND CENTER) ---
    if st.session_state.current_view == 'home':
        st.markdown("<h1><span style='color: #06b6d4;'>⚛</span> COMMAND NODE</h1>", unsafe_allow_html=True)
        
        # Sector Analytics Matrix with Fixed Plotly Colors
        sector_counts = {}
        for t in st.session_state.my_tickers:
            sec = TICKER_DATA.get(t, {}).get("sector", "Custom / Unclassified")
            sector_counts[sec] = sector_counts.get(sec, 0) + 1
            
        st.markdown("### ◴ SECTOR ALLOCATION MATRIX")
        if sector_counts:
            custom_colors = ["#06b6d4", "#0ea5e9", "#3b82f6", "#1e293b", "#0f172a", "#64748b", "#334155"]
            fig = px.pie(names=list(sector_counts.keys()), values=list(sector_counts.values()), hole=0.6, color_discrete_sequence=custom_colors)
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=0, r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("⎘ INJECT NEW ASSET")
        c1, c2 = st.columns([4, 1])
        with c1:
            new_asset = st.text_input("Enter Symbology (e.g., PLTR, SPY):", label_visibility="collapsed").strip().upper()
        with c2:
            st.markdown('<div class="add-btn">', unsafe_allow_html=True)
            if st.button("[+] APPEND"):
                add_ticker(new_asset)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        st.subheader(f"≣ ACTIVE WATCHLIST ({len(st.session_state.my_tickers)}/50)")
        
        for ticker in st.session_state.my_tickers:
            t_info = TICKER_DATA.get(ticker, {"name": "Custom Asset"})
            col1, col2, col3, col4 = st.columns([1, 4, 2, 1.5])
            
            with col1: st.markdown(f"**{ticker}**")
            with col2: st.markdown(f"<span style='color: #94a3b8;'>{t_info['name']}</span>", unsafe_allow_html=True)
            
            with col3: 
                st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                st.button("[~] EXECUTE", key=f"view_{ticker}", on_click=go_to_detail, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
            with col4: 
                st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
                st.button("[x] DROP", key=f"rem_{ticker}", on_click=remove_ticker, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<hr style='margin: 0.2em 0; border: 0.5px solid #1e293b;'>", unsafe_allow_html=True)

    # --- DETAIL PAGE ---
    elif st.session_state.current_view == 'detail':
        ticker_sym = st.session_state.active_ticker
        t_info = TICKER_DATA.get(ticker_sym, {"name": ""})
        title_display = f"{ticker_sym} // {t_info['name']}" if t_info['name'] else ticker_sym
        
        c1, c2 = st.columns([4, 1])
        with c1: st.markdown(f"<h1><span style='color: #06b6d4;'>⚛</span> {title_display}</h1>", unsafe_allow_html=True)
        with c2: st.button("[<] RETURN", on_click=go_to_home, use_container_width=True)
        
        with st.spinner(f"Establishing secure telemetry for {ticker_sym}..."):
            df = get_cached_history(ticker_sym)
            
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
            m4.metric("Telemetry Window", "90 Days")
            st.write("---")
            
            chart_type = st.radio("Visualization Matrix:", ["Standard Output", "Pro (Candlestick)"], horizontal=True)
            
            if chart_type == "Standard Output":
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
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0), height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"ERR_DATA_NULL: Telemetry for {ticker_sym} failed. Asset may be delisted.")
