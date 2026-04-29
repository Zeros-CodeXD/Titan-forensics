import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# --- 1. SETTINGS & MODERN APP CSS ---
st.set_page_config(page_title="Titan V12", page_icon="⚛", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #0f172a 0%, #020617 100%); background-size: cover; color: #e2e8f0; }
    h1, h2, h3 { color: #38bdf8; font-family: 'Courier New', Courier, monospace; letter-spacing: 1px;}
    div[data-testid="column"] { display: flex; align-items: center; }
    .stButton>button, .stButton>button * { border-radius: 6px; font-weight: 800; width: 100%; transition: all 0.2s ease; border: none !important; color: #0f172a !important; }
    .add-btn .stButton>button { background: #0ea5e9 !important; box-shadow: 0px 4px 10px rgba(14, 165, 233, 0.3); }
    .add-btn .stButton>button:hover { background: #38bdf8 !important; transform: translateY(-2px); }
    .action-btn .stButton>button { background: #3b82f6 !important; box-shadow: 0px 4px 10px rgba(59, 130, 246, 0.3); }
    .action-btn .stButton>button:hover { background: #60a5fa !important; transform: scale(1.02); }
    .remove-btn .stButton>button { background: #f87171 !important; box-shadow: 0px 4px 10px rgba(248, 113, 113, 0.2); }
    .remove-btn .stButton>button:hover { background: #fca5a5 !important; transform: scale(1.02); }
    .auth-box { background: #0f172a; padding: 2rem; border-radius: 8px; border: 1px solid #1e293b; border-left: 4px solid #3b82f6; box-shadow: 0px 10px 30px rgba(0,0,0,0.5);}
    .hero-title { text-align: center; padding: 3rem 0 1rem 0; }
    .hero-title h1 { font-size: 4.5rem; margin-bottom: 0; text-shadow: 0px 0px 20px rgba(14, 165, 233, 0.4); }
    .hero-title h3 { color: #64748b; margin-top: 0; letter-spacing: 5px; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CLOUD INFRASTRUCTURE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()
cookie_controller = CookieController() # Initialize the Browser Cookie Manager

# --- 3. DATA DICTIONARIES ---
TICKER_DATA = {
    "AAPL": {"name": "Apple Inc.", "domain": "apple.com", "sector": "Technology"},
    "MSFT": {"name": "Microsoft", "domain": "microsoft.com", "sector": "Technology"},
    "GOOGL": {"name": "Alphabet", "domain": "abc.xyz", "sector": "Communication"},
    "AMZN": {"name": "Amazon", "domain": "amazon.com", "sector": "Consumer Cyclical"},
    "META": {"name": "Meta Platforms", "domain": "meta.com", "sector": "Communication"},
    "TSLA": {"name": "Tesla", "domain": "tesla.com", "sector": "Consumer Cyclical"},
    "NVDA": {"name": "NVIDIA", "domain": "nvidia.com", "sector": "Technology"},
    "NFLX": {"name": "Netflix", "domain": "netflix.com", "sector": "Communication"},
    "AMD": {"name": "Advanced Micro Devices", "domain": "amd.com", "sector": "Technology"},
    "INTC": {"name": "Intel", "domain": "intel.com", "sector": "Technology"},
    "BA": {"name": "Boeing", "domain": "boeing.com", "sector": "Industrials"},
    "DIS": {"name": "Disney", "domain": "thewaltdisneycompany.com", "sector": "Communication"},
    "V": {"name": "Visa", "domain": "visa.com", "sector": "Financials"},
    "JPM": {"name": "JPMorgan Chase", "domain": "jpmorganchase.com", "sector": "Financials"},
    "WMT": {"name": "Walmart", "domain": "walmart.com", "sector": "Consumer Defensive"},
    "T": {"name": "AT&T", "domain": "att.com", "sector": "Communication"},
    "XOM": {"name": "Exxon Mobil", "domain": "exxonmobil.com", "sector": "Energy"},
    "CVX": {"name": "Chevron", "domain": "chevron.com", "sector": "Energy"},
    "PG": {"name": "Procter & Gamble", "domain": "pg.com", "sector": "Consumer Defensive"},
    "KO": {"name": "Coca-Cola", "domain": "coca-colacompany.com", "sector": "Consumer Defensive"},
    "PEP": {"name": "PepsiCo", "domain": "pepsico.com", "sector": "Consumer Defensive"},
    "CSCO": {"name": "Cisco", "domain": "cisco.com", "sector": "Technology"},
    "PFE": {"name": "Pfizer", "domain": "pfizer.com", "sector": "Healthcare"},
    "MRK": {"name": "Merck", "domain": "merck.com", "sector": "Healthcare"},
    "ABBV": {"name": "AbbVie", "domain": "abbvie.com", "sector": "Healthcare"}
}
DEFAULT_TICKERS = list(TICKER_DATA.keys())

# --- 4. SESSION & COOKIE STATE MANAGEMENT ---
if 'current_view' not in st.session_state: st.session_state.current_view = 'home'
if 'active_ticker' not in st.session_state: st.session_state.active_ticker = None
if 'my_tickers' not in st.session_state: st.session_state.my_tickers = DEFAULT_TICKERS.copy()

# Automatically check for existing browser cookies on boot
saved_cookie = cookie_controller.get("titan_session")

if 'user_email' not in st.session_state: 
    if saved_cookie:
        st.session_state.user_email = saved_cookie
    else:
        st.session_state.user_email = None

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

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_history(ticker_sym):
    try:
        stock = yf.Ticker(ticker_sym)
        return stock.history(period="3mo")
    except Exception:
        return pd.DataFrame()

# If the app just booted up from a cookie, make sure we pull their specific data
if st.session_state.user_email and st.session_state.my_tickers == DEFAULT_TICKERS:
    load_user_data()

# --- 6. AUTHENTICATION GATEWAY ---
if st.session_state.user_email is None:
    st.markdown("<div class='hero-title'><h1><span style='color: #0ea5e9;'>⚛</span> TITAN</h1><h3>MACRO-FORENSICS</h3></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Secure Institutional Terminal • Authorized Personnel Only</p><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        auth_mode = st.radio("System Access:", ["Authenticate", "Request Allocation"], horizontal=True)
        email = st.text_input("Operator ID (Email)")
        password = st.text_input("Encryption Key (Password)", type="password")
        
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        if st.button("🔐 INITIATE HANDSHAKE"):
            if auth_mode == "Request Allocation":
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Credentials logged. Proceed to authenticate.")
                except Exception as e:
                    st.error(f"Registration Error: {e}")
            elif auth_mode == "Authenticate":
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    # 1. Update session
                    st.session_state.user_email = res.user.email
                    # 2. Write the cookie to the browser so they never have to log in again
                    cookie_controller.set("titan_session", res.user.email)
                    # 3. Pull their data
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
        st.markdown(f"<div style='background-color: #0f172a; padding: 10px; border-radius: 6px; border-left: 3px solid #3b82f6; font-family: monospace;'><b>USER:</b><br>{st.session_state.user_email}</div><br>", unsafe_allow_html=True)
        st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
        if st.button("🔒 TERMINATE SESSION"):
            # 1. Sign out of database
            supabase.auth.sign_out()
            # 2. Delete the browser cookie
            cookie_controller.remove("titan_session")
            # 3. Wipe memory
            st.session_state.user_email = None
            st.session_state.my_tickers = DEFAULT_TICKERS.copy()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- HOME PAGE (COMMAND CENTER) ---
    if st.session_state.current_view == 'home':
        
        st.markdown("<div class='hero-title'><h1><span style='color: #0ea5e9;'>⚛</span> TITAN</h1><h3>MACRO-FORENSICS TERMINAL</h3></div>", unsafe_allow_html=True)
        st.divider()

        st.subheader("⎘ INJECT NEW ASSET")
        c1, c2 = st.columns([4, 1])
        with c1:
            new_asset = st.text_input("Enter Symbology (e.g., PLTR, SPY):", label_visibility="collapsed").strip().upper()
        with c2:
            st.markdown('<div class="add-btn">', unsafe_allow_html=True)
            if st.button("➕ ADD TO INDEX"):
                add_ticker(new_asset)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        st.subheader(f"≣ ACTIVE WATCHLIST ({len(st.session_state.my_tickers)}/50)")
        
        for ticker in st.session_state.my_tickers:
            t_info = TICKER_DATA.get(ticker, {"name": "Custom Asset", "domain": ""})
            domain = t_info.get("domain", "")
            fallback_url = f"https://ui-avatars.com/api/?name={ticker}&background=0f172a&color=0ea5e9&bold=true"
            logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128" if domain else fallback_url
            
            col1, col2, col3, col4 = st.columns([1.5, 3.5, 2, 1.5])
            
            with col1: 
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 12px; padding-top: 4px;">
                        <img src="{logo_url}" onerror="this.onerror=null; this.src='{fallback_url}';" width="30" height="30" style="border-radius: 6px; object-fit: contain; background-color: #ffffff; padding: 2px;">
                        <span style="font-weight: bold; font-size: 1.1em;">{ticker}</span>
                    </div>
                """, unsafe_allow_html=True)
                
            with col2: 
                st.markdown(f"<div style='color: #94a3b8; padding-top: 8px;'>{t_info['name']}</div>", unsafe_allow_html=True)
            
            with col3: 
                st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                st.button("🔍 ANALYZE", key=f"view_{ticker}", on_click=go_to_detail, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
            with col4: 
                st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
                st.button("❌ REMOVE", key=f"rem_{ticker}", on_click=remove_ticker, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<hr style='margin: 0.2em 0; border: 0.5px solid #1e293b;'>", unsafe_allow_html=True)

    # --- DETAIL PAGE ---
    elif st.session_state.current_view == 'detail':
        ticker_sym = st.session_state.active_ticker
        t_info = TICKER_DATA.get(ticker_sym, {"name": "", "domain": ""})
        domain = t_info.get("domain", "")
        fallback_url = f"https://ui-avatars.com/api/?name={ticker_sym}&background=0f172a&color=0ea5e9&bold=true"
        logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128" if domain else fallback_url
        
        c1, c2 = st.columns([4, 1])
        with c1: 
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 15px;">
                    <img src="{logo_url}" onerror="this.onerror=null; this.src='{fallback_url}';" width="40" height="40" style="border-radius: 8px; object-fit: contain; background-color: #ffffff; padding: 2px;">
                    <h1 style="margin: 0;"><span style='color: #0ea5e9;'>⚛</span> {ticker_sym} <span style="font-size: 0.6em; color: #64748b;">// {t_info['name']}</span></h1>
                </div>
            """, unsafe_allow_html=True)
            
        with c2: 
            st.markdown('<div class="action-btn">', unsafe_allow_html=True)
            st.button("⬅ RETURN", on_click=go_to_home, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("")
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
                    st.line_chart(df['Close'], color="#0ea5e9")
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
