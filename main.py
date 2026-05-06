import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController
from datetime import datetime

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
    .stTextInput>div>div>input, .stSelectbox>div>div>div { 
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
    .ticker-card:hover { border-color: #00e5ff; background: #0f1a2e; }

    /* Metric UI */
    div[data-testid="stMetricValue"] > div { color: #00fa9a !important; font-family: monospace; font-size: 1.8rem; }
    div[data-testid="stMetricDelta"] > div { color: #00e5ff !important; }

    /* Tab Styling & News Cards */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent !important; gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-weight: 800; border-bottom: 2px solid transparent; }
    .stTabs [aria-selected="true"] { color: #00e5ff !important; border-bottom: 2px solid #00e5ff !important; background: transparent !important;}
    
    .news-card { background: #0b1221; border-left: 3px solid #00fa9a; padding: 15px; margin-bottom: 15px; border-radius: 4px; border-right: 1px solid #1e293b; border-top: 1px solid #1e293b; border-bottom: 1px solid #1e293b;}
    .news-card a { color: #00e5ff !important; text-decoration: none; font-size: 1.1rem; font-weight: bold; }
    .news-card a:hover { text-decoration: underline; text-shadow: 0px 0px 5px rgba(0, 229, 255, 0.5); }
    .news-date { color: #64748b !important; font-size: 0.8rem; margin-top: 5px; font-family: monospace;}
    
    /* Fundamental Key-Value styling */
    .fund-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px dashed #1e293b; }
    .fund-key { color: #94a3b8 !important; }
    .fund-val { color: #00fa9a !important; font-family: monospace; font-weight: bold; font-size: 1.1rem; }
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
    "NFLX": {"name": "Netflix", "domain": "netflix.com", "sector": "Communication"}
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

# --- 5. SECURE DATABASE & ADVANCED METADATA LOGIC ---
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

@st.cache_data(ttl=900, show_spinner=False) # Cached for 15 mins for pseudo-realtime
def get_cached_history(ticker_sym, period="3mo"):
    try:
        stock = yf.Ticker(ticker_sym)
        df = stock.history(period=period)
        if not df.empty:
            # Calculate Technical Indicators
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=86400, show_spinner=False)
def get_dynamic_info(ticker_sym):
    try:
        stock = yf.Ticker(ticker_sym)
        info = stock.info
        name = info.get("shortName", ticker_sym)
        domain = info.get("website", "").replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        return name, domain
    except Exception:
        return ticker_sym, ""

@st.cache_data(ttl=1800, show_spinner=False) # Cache intel for 30 mins
def get_full_intel(ticker_sym):
    try:
        stock = yf.Ticker(ticker_sym)
        return stock.info, stock.news
    except Exception:
        return {}, []

def format_large_number(num):
    if not isinstance(num, (int, float)) or pd.isna(num): return "N/A"
    if num >= 1e12: return f"${num/1e12:.2f}T"
    if num >= 1e9: return f"${num/1e9:.2f}B"
    if num >= 1e6: return f"${num/1e6:.2f}M"
    return f"${num:,.2f}"

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

    # --- SIDEBAR CONTROL PANEL ---
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
        
        for ticker in st.session_state.my_tickers:
            if ticker in TICKER_DATA:
                t_name, t_domain = TICKER_DATA[ticker]["name"], TICKER_DATA[ticker]["domain"]
            else:
                t_name, t_domain = get_dynamic_info(ticker)
            
            fallback_url = f"https://ui-avatars.com/api/?name={ticker}&background=0f172a&color=00e5ff&bold=true&font-size=0.33"
            logo_url = f"https://icon.horse/icon/{t_domain}" if t_domain else fallback_url
            
            st.markdown('<div class="ticker-card">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([0.5, 3, 1, 1])
            with col1: 
                st.markdown(f"""<img src="{logo_url}" style="width: 38px; height: 38px; border-radius: 6px; object-fit: contain; background-color: transparent;">""", unsafe_allow_html=True)
            with col2: 
                st.markdown(f"<div style='padding-top: 5px;'><span style='font-size: 1.2rem; font-weight: bold; color: #00e5ff !important;'>{ticker}</span> <span style='color: #64748b !important;'>// {t_name}</span></div>", unsafe_allow_html=True)
            with col3: 
                st.button("🔍 ANALYZE", key=f"view_{ticker}", on_click=go_to_detail, args=(ticker,))
            with col4: 
                st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
                st.button("❌ PURGE", key=f"rem_{ticker}", on_click=remove_ticker, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- DETAIL PAGE (ADVANCED MATRIX) ---
    elif st.session_state.current_view == 'detail':
        ticker_sym = st.session_state.active_ticker
        
        if ticker_sym in TICKER_DATA:
            t_name, t_domain = TICKER_DATA[ticker_sym]["name"], TICKER_DATA[ticker_sym]["domain"]
        else:
            t_name, t_domain = get_dynamic_info(ticker_sym)
            
        fallback_url = f"https://ui-avatars.com/api/?name={ticker_sym}&background=0f172a&color=00e5ff&bold=true&font-size=0.33"
        logo_url = f"https://icon.horse/icon/{t_domain}" if t_domain else fallback_url
        
        c1, c2 = st.columns([5, 1])
        with c1: 
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 15px;">
                    <img src="{logo_url}" style="width: 50px; height: 50px; border-radius: 8px; object-fit: contain; background-color: transparent;">
                    <h1 style="margin: 0;">{ticker_sym} <span style="font-size: 0.5em; color: #64748b !important;">// {t_name}</span></h1>
                </div>
            """, unsafe_allow_html=True)
        with c2: 
            st.button("⬅ RETURN TO INDEX", on_click=go_to_home, use_container_width=True)
        
        st.markdown("<hr style='border-color: #1e293b; margin: 15px 0;'>", unsafe_allow_html=True)

        # Tabbed Layout for Pro Feel
        tab1, tab2, tab3 = st.tabs(["🎛️ TELEMETRY MATRIX", "📊 FUNDAMENTAL DATA", "📰 LIVE INTELLIGENCE"])

        with st.spinner(f"ESTABLISHING SECURE DATALINK FOR {ticker_sym}..."):
            info_data, news_data = get_full_intel(ticker_sym)
            
        # --- TAB 1: CHARTING & PRICE ACTION ---
        with tab1:
            control_col, spacer = st.columns([2, 5])
            with control_col:
                selected_period = st.selectbox("TIMEFRAME WINDOW:", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=1)
            
            df = get_cached_history(ticker_sym, period=selected_period)
            
            if not df.empty:
                latest_close = df['Close'].iloc[-1]
                latest_open = df['Open'].iloc[-1]
                latest_vol = df['Volume'].iloc[-1]
                price_delta = latest_close - df['Close'].iloc[-2]
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("LATEST CLOSE", f"${latest_close:,.2f}", f"{price_delta:,.2f}")
                m2.metric("LATEST OPEN", f"${latest_open:,.2f}")
                m3.metric("TRADE VOLUME", f"{latest_vol:,.0f}")
                m4.metric("WINDOW RANGE", selected_period.upper())
                st.write("")
                
                chart_type = st.radio("VISUALIZATION MATRIX:", ["PRO (CANDLESTICK + SMA)", "STANDARD OUTPUT"], horizontal=True)
                
                if chart_type == "STANDARD OUTPUT":
                    col1, col2 = st.columns([2, 1])
                    with col1: 
                        st.markdown("### PRICE ACTION TREND")
                        st.line_chart(df['Close'], color="#00e5ff")
                    with col2: 
                        st.markdown("### INSTITUTIONAL VOLUME")
                        st.bar_chart(df['Volume'], color="#00fa9a")
                else: 
                    st.markdown("### CANDLESTICK & MOVING AVERAGES")
                    fig = go.Figure()
                    
                    # Candlestick Trace
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                        increasing_line_color='#00fa9a', decreasing_line_color='#ff2a6d', name="Price"
                    ))
                    # Moving Average Traces
                    if 'SMA_20' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#00e5ff', width=1.5), name='20-Day SMA'))
                    if 'SMA_50' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#f59e0b', width=1.5), name='50-Day SMA'))

                    fig.update_layout(
                        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                        margin=dict(l=0, r=0, t=30, b=0), height=500, font=dict(color="#94a3b8"),
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                    )
                    fig.update_xaxes(showgrid=False, zeroline=False)
                    fig.update_yaxes(showgrid=True, gridcolor='#1e293b', zeroline=False)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"ERR_DATA_NULL: TELEMETRY FAILED.", icon="⚠")

        # --- TAB 2: FUNDAMENTALS ---
        with tab2:
            st.markdown("### MACRO-ECONOMIC FUNDAMENTALS")
            if info_data:
                f1, f2 = st.columns(2)
                with f1:
                    st.markdown(f"<div class='fund-row'><span class='fund-key'>Market Capitalization</span><span class='fund-val'>{format_large_number(info_data.get('marketCap'))}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='fund-row'><span class='fund-key'>Trailing P/E Ratio</span><span class='fund-val'>{info_data.get('trailingPE', 'N/A')}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='fund-row'><span class='fund-key'>Forward P/E Ratio</span><span class='fund-val'>{info_data.get('forwardPE', 'N/A')}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='fund-row'><span class='fund-key'>Dividend Yield</span><span class='fund-val'>{info_data.get('dividendYield', 0)*100:.2f}%</span></div>", unsafe_allow_html=True)
                with f2:
                    st.markdown(f"<div class='fund-row'><span class='fund-key'>52 Week High</span><span class='fund-val'>${info_data.get('fiftyTwoWeekHigh', 'N/A')}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='fund-row'><span class='fund-key'>52 Week Low</span><span class='fund-val'>${info_data.get('fiftyTwoWeekLow', 'N/A')}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='fund-row'><span class='fund-key'>Average Volume (10d)</span><span class='fund-val'>{format_large_number(info_data.get('averageVolume10days'))}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='fund-row'><span class='fund-key'>Sector</span><span class='fund-val'>{info_data.get('sector', 'N/A').upper()}</span></div>", unsafe_allow_html=True)
                
                st.write("")
                st.markdown("#### COMPANY PROFILE")
                st.markdown(f"<p style='color: #94a3b8 !important; line-height: 1.6;'>{info_data.get('longBusinessSummary', 'Profile data unavailable.')}</p>", unsafe_allow_html=True)
            else:
                st.warning("FUNDAMENTAL DATA UNAVAILABLE FOR THIS ASSET.")

        # --- TAB 3: NEWS FEED ---
        with tab3:
            st.markdown("### LATEST MARKET INTELLIGENCE")
            if news_data:
                for article in news_data[:6]: # Show top 6
                    title = article.get('title', 'Unknown Intel')
                    publisher = article.get('publisher', 'Unknown Source')
                    link = article.get('link', '#')
                    # Parse unix timestamp if available
                    pub_time = article.get('providerPublishTime')
                    date_str = datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d %H:%M:%S UTC') if pub_time else "Recent"
                    
                    st.markdown(f"""
                        <div class="news-card">
                            <a href="{link}" target="_blank">{title}</a>
                            <div class="news-date">SOURCE: {publisher.upper()} // LOGGED: {date_str}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("NO RECENT INTELLIGENCE LOGGED FOR THIS ASSET.")
