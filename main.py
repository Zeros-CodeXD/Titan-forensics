import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# --- 1. SETTINGS & STRICT NON-WHITE TERMINAL CSS ---
st.set_page_config(page_title="Titan Terminal", page_icon="⚛", layout="wide")

st.markdown("""
    <style>
    /* Global App Background - Deep Obsidian/Navy */
    .stApp { 
        background: radial-gradient(circle at top, #080d17 0%, #03070b 100%); 
        background-size: cover; 
    }
    
    /* ENFORCING NO-WHITE RULE FOR ALL TEXT & FEATURES */
    p, span, div, label, li { color: #94a3b8 !important; }
    h1, h2, h3, h4, h5, h6 { 
        color: #00e5ff !important; 
        font-family: 'Courier New', Courier, monospace; 
        letter-spacing: 2px;
        text-shadow: 0px 0px 8px rgba(0, 229, 255, 0.3);
    }
    
    /* Inputs & Selectors */
    .stTextInput>div>div>input { 
        background-color: #0f172a !important; 
        color: #00e5ff !important; 
        border: 1px solid #1e293b !important; 
    }
    .stTextInput>div>div>input:focus {
        border-color: #00e5ff !important;
        box-shadow: 0 0 8px rgba(0, 229, 255, 0.4) !important;
    }
    .stRadio label, .stCheckbox label { color: #00e5ff !important; }

    /* Universal Button Styling (No White) */
    .stButton>button { 
        border-radius: 4px; 
        font-weight: 800; 
        letter-spacing: 1px;
        width: 100%; 
        transition: all 0.3s ease; 
        background: #0f172a !important; 
        color: #00e5ff !important;
        border: 1px solid #00e5ff !important; 
    }
    .stButton>button:hover { 
        background: #00e5ff !important; 
        color: #03070b !important; 
        box-shadow: 0px 0px 15px rgba(0, 229, 255, 0.5); 
        transform: translateY(-2px);
    }
    
    /* Specific Action Buttons */
    .add-btn .stButton>button { border-color: #00fa9a !important; color: #00fa9a !important; }
    .add-btn .stButton>button:hover { background: #00fa9a !important; color: #03070b !important; box-shadow: 0px 0px 15px rgba(0, 250, 154, 0.5); }
    
    .remove-btn .stButton>button { border-color: #ff2a6d !important; color: #ff2a6d !important; }
    .remove-btn .stButton>button:hover { background: #ff2a6d !important; color: #03070b !important; box-shadow: 0px 0px 15px rgba(255, 42, 109, 0.5); }

    /* Better Login UI */
    .auth-box { 
        background: rgba(15, 23, 42, 0.6); 
        backdrop-filter: blur(10px);
        padding: 3rem; 
        border-radius: 12px; 
        border: 1px solid #1e293b; 
        border-top: 4px solid #00e5ff; 
        box-shadow: 0px 15px 40px rgba(0, 229, 255, 0.05);
    }
    
    /* Custom Ticker Card UI */
    .ticker-card {
        background: #0b1221;
        border: 1px solid #1e293b;
        border-left: 4px solid #00e5ff;
        border-radius: 6px;
        padding: 10px 15px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .ticker-card:hover {
        border-color: #00e5ff;
        background: #0f1a2e;
    }

    /* Metric UI */
    div[data-testid="stMetricValue"] > div { color: #00fa9a !important; font-family: monospace; font-size: 1.8rem; }
    div[data-testid="stMetricDelta"] > div { color: #00e5ff !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CLOUD INFRASTRUCTURE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()
cookie_controller = CookieController()

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

saved_cookie = cookie_controller.get("titan_session")

if 'user_email' not in st.session_state: 
    if saved_cookie:
        st.session_state.user_email = saved_cookie
    else:
        st.session_state.user_email = None

# --- 5. SECURE DATABASE & METADATA LOGIC ---
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

@st.cache_data(ttl=86400, show_spinner=False)
def get_dynamic_info(ticker_sym):
    try:
        stock = yf.Ticker(ticker_sym)
        info = stock.info
        name = info.get("shortName", ticker_sym)
        website = info.get("website", "")
        domain = ""
        if website:
            domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        return name, domain
    except Exception:
        return ticker_sym, ""

if st.session_state.user_email and st.session_state.my_tickers == DEFAULT_TICKERS:
    load_user_data()

# --- 6. AUTHENTICATION GATEWAY ---
if st.session_state.user_email is None:
    st.write("")
    st.write("")
    st.markdown("<h1 style='text-align: center; font-size: 5rem;'><span style='color: #00e5ff;'>⚛</span> TITAN</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #64748b !important; letter-spacing: 5px;'>SYSTEM ACCESS GATEWAY</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        auth_mode = st.radio("SELECT MODE:", ["AUTHENTICATE", "REQUEST ALLOCATION"], horizontal=True)
        st.write("")
        email = st.text_input("OPERATOR ID (EMAIL)")
        password = st.text_input("ENCRYPTION KEY (PASSWORD)", type="password")
        st.write("")
        
        if st.button("🔐 INITIATE SECURE HANDSHAKE"):
            if auth_mode == "REQUEST ALLOCATION":
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("CREDENTIALS LOGGED. PROCEED TO AUTHENTICATE.", icon="✅")
                except Exception as e:
                    st.error(f"REGISTRATION ERR: {e}")
            elif auth_mode == "AUTHENTICATE":
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user_email = res.user.email
                    cookie_controller.set("titan_session", res.user.email)
                    load_user_data() 
                    st.rerun() 
                except Exception as e:
                    st.error("ERR_CONNECTION_REFUSED: INVALID CREDENTIALS.", icon="❌")
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
                st.error("ERR_MEMORY_FULL: MAX 50 ASSETS PERMITTED.")

    # --- BETTER LOGOUT & SIDEBAR ---
    with st.sidebar:
        st.markdown("## ⎈ CONTROL PANEL")
        st.markdown(f"""
            <div style='background-color: #0b1221; padding: 15px; border-radius: 6px; border: 1px solid #1e293b; border-left: 4px solid #00fa9a;'>
                <p style='color: #00fa9a !important; font-size: 0.8rem; margin:0;'>STATUS: SECURE LINK ACTIVE</p>
                <p style='color: #00e5ff !important; font-family: monospace; margin: 10px 0 0 0; font-size: 1.1rem; word-wrap: break-word;'>{st.session_state.user_email}</p>
            </div><br>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
        if st.button("🔌 SEVER CONNECTION (LOGOUT)"):
            supabase.auth.sign_out()
            cookie_controller.remove("titan_session")
            st.session_state.user_email = None
            st.session_state.my_tickers = DEFAULT_TICKERS.copy()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- HOME PAGE (COMMAND CENTER) ---
    if st.session_state.current_view == 'home':
        st.markdown("<h1><span style='color: #00e5ff;'>⚛</span> TITAN TERMINAL // MACRO-FORENSICS</h1>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)

        st.markdown("### ⎘ INJECT NEW ASSET SYMBOLOGY")
        c1, c2 = st.columns([5, 1])
        with c1:
            new_asset = st.text_input("TICKER INPUT", placeholder="e.g., PLTR, SPY, RELIANCE.NS", label_visibility="collapsed").strip().upper()
        with c2:
            st.markdown('<div class="add-btn">', unsafe_allow_html=True)
            if st.button("➕ ADD ASSET"):
                add_ticker(new_asset)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown(f"### ≣ ACTIVE INDEX ALLOCATION ({len(st.session_state.my_tickers)}/50)")
        
        # Grid layout for tickers
        for ticker in st.session_state.my_tickers:
            if ticker in TICKER_DATA:
                t_name = TICKER_DATA[ticker]["name"]
                t_domain = TICKER_DATA[ticker]["domain"]
            else:
                t_name, t_domain = get_dynamic_info(ticker)
            
            # Using Clearbit for crisp logos, UI-Avatars for fallback. NO WHITE BACKGROUNDS.
            fallback_url = f"https://ui-avatars.com/api/?name={ticker}&background=0f172a&color=00e5ff&bold=true&font-size=0.33"
            logo_url = f"https://logo.clearbit.com/{t_domain}" if t_domain else fallback_url
            
            # Container for the row to maintain alignment
            st.markdown('<div class="ticker-card">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([0.5, 3, 1, 1])
            
            with col1: 
                # Removed the white background from the styling block.
                st.markdown(f"""
                    <img src="{logo_url}" onerror="this.onerror=null; this.src='{fallback_url}';" 
                    style="width: 38px; height: 38px; border-radius: 6px; object-fit: contain; background-color: transparent;">
                """, unsafe_allow_html=True)
                
            with col2: 
                st.markdown(f"<div style='padding-top: 5px;'><span style='font-size: 1.2rem; font-weight: bold; color: #00e5ff !important;'>{ticker}</span> <span style='color: #64748b !important;'>// {t_name}</span></div>", unsafe_allow_html=True)
            
            with col3: 
                st.button("🔍 ANALYZE", key=f"view_{ticker}", on_click=go_to_detail, args=(ticker,))
            with col4: 
                st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
                st.button("❌ PURGE", key=f"rem_{ticker}", on_click=remove_ticker, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- DETAIL PAGE ---
    elif st.session_state.current_view == 'detail':
        ticker_sym = st.session_state.active_ticker
        
        if ticker_sym in TICKER_DATA:
            t_name = TICKER_DATA[ticker_sym]["name"]
            t_domain = TICKER_DATA[ticker_sym]["domain"]
        else:
            t_name, t_domain = get_dynamic_info(ticker_sym)
            
        fallback_url = f"https://ui-avatars.com/api/?name={ticker_sym}&background=0f172a&color=00e5ff&bold=true&font-size=0.33"
        logo_url = f"https://logo.clearbit.com/{t_domain}" if t_domain else fallback_url
        
        c1, c2 = st.columns([5, 1])
        with c1: 
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 15px;">
                    <img src="{logo_url}" onerror="this.onerror=null; this.src='{fallback_url}';" style="width: 50px; height: 50px; border-radius: 8px; object-fit: contain; background-color: transparent;">
                    <h1 style="margin: 0;">{ticker_sym} <span style="font-size: 0.5em; color: #64748b !important;">// {t_name}</span></h1>
                </div>
            """, unsafe_allow_html=True)
            
        with col2: 
            st.button("⬅ RETURN TO INDEX", on_click=go_to_home, use_container_width=True)
        
        st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)
        
        with st.spinner(f"ESTABLISHING SECURE TELEMETRY FOR {ticker_sym}..."):
            df = get_cached_history(ticker_sym)
            
        if not df.empty:
            latest_close = df['Close'].iloc[-1]
            latest_open = df['Open'].iloc[-1]
            latest_vol = df['Volume'].iloc[-1]
            price_delta = latest_close - df['Close'].iloc[-2]
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("LATEST CLOSE", f"${latest_close:,.2f}", f"{price_delta:,.2f}")
            m2.metric("LATEST OPEN", f"${latest_open:,.2f}")
            m3.metric("TRADE VOLUME", f"{latest_vol:,.0f}")
            m4.metric("TELEMETRY WINDOW", "90 DAYS")
            st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)
            
            chart_type = st.radio("VISUALIZATION MATRIX:", ["STANDARD OUTPUT", "PRO (CANDLESTICK)"], horizontal=True)
            
            if chart_type == "STANDARD OUTPUT":
                col1, col2 = st.columns([2, 1])
                with col1: 
                    st.markdown("### PRICE ACTION TREND")
                    # Enforcing the specific cyan color on native charts
                    st.line_chart(df['Close'], color="#00e5ff")
                with col2: 
                    st.markdown("### INSTITUTIONAL VOLUME")
                    st.bar_chart(df['Volume'], color="#00fa9a")
            else: 
                st.markdown("### CANDLESTICK PRICE ACTION")
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index, 
                    open=df['Open'], 
                    high=df['High'], 
                    low=df['Low'], 
                    close=df['Close'],
                    increasing_line_color='#00fa9a',  # Emerald for up
                    decreasing_line_color='#ff2a6d'   # Ruby Red for down
                )])
                fig.update_layout(
                    template="plotly_dark", 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    margin=dict(l=0, r=0, t=0, b=0), 
                    height=450,
                    font=dict(color="#94a3b8") # Ensures chart labels aren't white
                )
                fig.update_xaxes(showgrid=False, zeroline=False)
                fig.update_yaxes(showgrid=True, gridcolor='#1e293b', zeroline=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"ERR_DATA_NULL: TELEMETRY FOR {ticker_sym} FAILED. VERIFY TICKER ACCURACY.", icon="⚠")
