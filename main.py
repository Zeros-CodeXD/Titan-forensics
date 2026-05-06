import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController
from datetime import datetime

# --- 1. SETTINGS & INSTITUTIONAL CSS ---
st.set_page_config(page_title="Titan Institutional | V2", page_icon="🏛", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* Global Styles */
    .stApp { background-color: #0A0A0A; color: #F8FAFC; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4 { font-family: 'Inter', sans-serif; font-weight: 800; color: #FFFFFF; }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Modern Glass Cards */
    .glass-card { background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.08); backdrop-filter: blur(12px); border-radius: 12px; padding: 24px; margin-bottom: 16px; transition: transform 0.2s ease, box-shadow 0.2s ease; }
    .glass-card:hover { border-color: rgba(56, 189, 248, 0.4); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); }
    
    /* Button Overhauls */
    .stButton>button { border-radius: 8px !important; font-weight: 600 !important; width: 100%; transition: all 0.3s ease !important; border: 1px solid transparent !important; text-transform: uppercase; letter-spacing: 0.5px; padding: 0.6rem 1.2rem !important; }
    
    .btn-primary .stButton>button { background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important; color: white !important; box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.3) !important; }
    .btn-primary .stButton>button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4) !important; border-color: rgba(255,255,255,0.2) !important; }
    
    .btn-danger .stButton>button { background: rgba(239, 68, 68, 0.1) !important; color: #ef4444 !important; border: 1px solid rgba(239, 68, 68, 0.3) !important; }
    .btn-danger .stButton>button:hover { background: rgba(239, 68, 68, 0.2) !important; border-color: #ef4444 !important; }

    .btn-ghost .stButton>button { background: rgba(255, 255, 255, 0.05) !important; color: #94a3b8 !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    .btn-ghost .stButton>button:hover { background: rgba(255, 255, 255, 0.1) !important; color: white !important; }

    /* Login Screen */
    .auth-wrapper { max-width: 450px; margin: 5rem auto; }
    .hero-title { text-align: center; margin-bottom: 2rem; }
    .hero-title h1 { font-size: 3.5rem; letter-spacing: -1px; margin-bottom: 0.5rem; background: -webkit-linear-gradient(45deg, #38bdf8, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .hero-title p { color: #64748b; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; }
    
    /* Metrics Override */
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800 !important; }
    div[data-testid="stMetricDelta"] svg { display: none; } /* Hide default arrow */
    
    hr { border-color: rgba(255,255,255,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- 2. CLOUD INFRASTRUCTURE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        st.error("Missing Supabase secrets. Please check your st.secrets file.")
        st.stop()

supabase = init_connection()
cookie_controller = CookieController()

# --- 3. DATA DICTIONARIES ---
TICKER_DATA = {
    "AAPL": {"name": "Apple Inc.", "domain": "apple.com"},
    "MSFT": {"name": "Microsoft", "domain": "microsoft.com"},
    "GOOGL": {"name": "Alphabet", "domain": "abc.xyz"},
    "AMZN": {"name": "Amazon", "domain": "amazon.com"},
    "TSLA": {"name": "Tesla", "domain": "tesla.com"},
    "NVDA": {"name": "NVIDIA", "domain": "nvidia.com"},
    "META": {"name": "Meta Platforms", "domain": "meta.com"},
    "JPM": {"name": "JPMorgan Chase", "domain": "jpmorganchase.com"},
    "V": {"name": "Visa", "domain": "visa.com"},
    "WMT": {"name": "Walmart", "domain": "walmart.com"}
}
DEFAULT_TICKERS = list(TICKER_DATA.keys())

# --- 4. SESSION MANAGEMENT ---
if 'current_view' not in st.session_state: st.session_state.current_view = 'home'
if 'active_ticker' not in st.session_state: st.session_state.active_ticker = None
if 'my_tickers' not in st.session_state: st.session_state.my_tickers = DEFAULT_TICKERS.copy()

saved_cookie = cookie_controller.get("titan_session")
if 'user_email' not in st.session_state: 
    st.session_state.user_email = saved_cookie if saved_cookie else None

# --- 5. ENHANCED DATA FETCHING (FREE/KEYLESS APIs) ---
def load_user_data():
    if st.session_state.user_email:
        res = supabase.table("secure_watchlists").select("tickers").eq("email", st.session_state.user_email).execute()
        if res.data: st.session_state.my_tickers = res.data[0]['tickers']
        else: save_user_data()

def save_user_data():
    if st.session_state.user_email:
        supabase.table("secure_watchlists").upsert({"email": st.session_state.user_email, "tickers": st.session_state.my_tickers}).execute()

@st.cache_data(ttl=900, show_spinner=False)
def get_cached_history(ticker_sym):
    try:
        stock = yf.Ticker(ticker_sym)
        df = stock.history(period="6mo")
        if not df.empty:
            # Calculate Moving Averages for pro chart
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
        return df, stock.info, stock.news
    except Exception:
        return pd.DataFrame(), {},[]

@st.cache_data(ttl=86400, show_spinner=False)
def get_dynamic_info(ticker_sym):
    try:
        info = yf.Ticker(ticker_sym).info
        name = info.get("shortName", ticker_sym)
        website = info.get("website", "")
        domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0] if website else ""
        return name, domain
    except:
        return ticker_sym, ""

if st.session_state.user_email and st.session_state.my_tickers == DEFAULT_TICKERS: load_user_data()

# --- 6. AUTHENTICATION GATEWAY (PROFESSIONAL UI) ---
if st.session_state.user_email is None:
    st.markdown("<div class='auth-wrapper'>", unsafe_allow_html=True)
    st.markdown("<div class='hero-title'><h1>TITAN Terminal</h1><p>Institutional Market Intelligence</p></div>", unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    auth_mode = st.radio("Authentication Required", ["Sign In", "Request Access"], horizontal=True, label_visibility="collapsed")
    st.write("")
    email = st.text_input("Institutional Email")
    password = st.text_input("Access Key", type="password")
    
    st.write("")
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
    if st.button("Initialize Secure Connection"):
        if auth_mode == "Request Access":
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Registration successful. You may now sign in.")
            except Exception as e: st.error(f"Error: {e}")
        else:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user_email = res.user.email
                cookie_controller.set("titan_session", res.user.email)
                load_user_data() 
                st.rerun() 
            except: st.error("Authentication Failed. Invalid Credentials.")
    st.markdown('</div></div></div>', unsafe_allow_html=True)

# --- 7. THE TERMINAL ---
else:
    # Routing Functions
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

    # --- SIDEBAR NAV ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Globe_icon_%28white%29.svg/2048px-Globe_icon_%28white%29.svg.png", width=40)
        st.markdown("### TITAN V2")
        st.markdown(f"<div style='color:#64748b; font-size: 12px;'>OPERATOR ID:<br><span style='color:#38bdf8;'>{st.session_state.user_email}</span></div><br>", unsafe_allow_html=True)
        
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("🏠 Dashboard"): go_to_home()
        st.markdown('</div><br><br>', unsafe_allow_html=True)
        
        st.markdown('<div class="btn-danger" style="position: absolute; bottom: 20px; width: 85%;">', unsafe_allow_html=True)
        if st.button("Disconnect Session"):
            supabase.auth.sign_out()
            cookie_controller.remove("titan_session")
            st.session_state.user_email = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- HOME DASHBOARD ---
    if st.session_state.current_view == 'home':
        st.markdown("<h2>Global Equities Portfolio</h2>", unsafe_allow_html=True)
        
        # Add Ticker Bar
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1])
        with c1:
            new_asset = st.text_input("Add Asset (e.g., PLTR, AAPL, RELIANCE.NS):", label_visibility="collapsed", placeholder="Enter Ticker Symbol...").strip().upper()
        with c2:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("+ Add Asset"):
                add_ticker(new_asset)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Watchlist Grid
        st.markdown(f"<h4 style='color:#94a3b8; font-size:14px; margin-top:30px;'>TRACKED ASSETS ({len(st.session_state.my_tickers)}/50)</h4>", unsafe_allow_html=True)
        
        for ticker in st.session_state.my_tickers:
            if ticker in TICKER_DATA:
                t_name, t_domain = TICKER_DATA[ticker]["name"], TICKER_DATA[ticker]["domain"]
            else:
                t_name, t_domain = get_dynamic_info(ticker)
            
            # Use High-Quality Clearbit Logo API
            fallback_url = f"https://ui-avatars.com/api/?name={ticker}&background=1e293b&color=38bdf8&bold=true"
            logo_url = f"https://logo.clearbit.com/{t_domain}" if t_domain else fallback_url
            
            st.markdown('<div class="glass-card" style="padding: 12px 24px; margin-bottom: 10px;">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([2, 4, 1.5, 1.5])
            
            with col1: 
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 16px; height: 100%;">
                        <img src="{logo_url}" onerror="this.onerror=null; this.src='{fallback_url}';" width="36" height="36" style="border-radius: 50%; object-fit: contain; background: white; padding: 4px;">
                        <span style="font-weight: 800; font-size: 1.2rem;">{ticker}</span>
                    </div>
                """, unsafe_allow_html=True)
            with col2: 
                st.markdown(f"<div style='color: #cbd5e1; font-weight: 400; padding-top: 8px;'>{t_name}</div>", unsafe_allow_html=True)
            with col3: 
                st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
                st.button("Analyze", key=f"view_{ticker}", on_click=go_to_detail, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
            with col4: 
                st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                st.button("Remove", key=f"rem_{ticker}", on_click=remove_ticker, args=(ticker,))
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- DETAIL ANALYSIS PAGE ---
    elif st.session_state.current_view == 'detail':
        ticker_sym = st.session_state.active_ticker
        
        t_name, t_domain = get_dynamic_info(ticker_sym)
        fallback_url = f"https://ui-avatars.com/api/?name={ticker_sym}&background=1e293b&color=38bdf8&bold=true"
        logo_url = f"https://logo.clearbit.com/{t_domain}" if t_domain else fallback_url
        
        # Header Row
        st.markdown('<div class="glass-card" style="padding: 15px 24px;">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1])
        with c1: 
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 20px;">
                    <img src="{logo_url}" onerror="this.onerror=null; this.src='{fallback_url}';" width="56" height="56" style="border-radius: 12px; background: white; padding: 6px;">
                    <div>
                        <h1 style="margin: 0; font-size: 2.2rem;">{ticker_sym}</h1>
                        <span style="color: #94a3b8; font-size: 1.1rem;">{t_name}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with c2: 
            st.markdown('<div class="btn-ghost" style="margin-top: 10px;">', unsafe_allow_html=True)
            st.button("Back", on_click=go_to_home)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.spinner(f"Aggregating market data for {ticker_sym}..."):
            df, info, news = get_cached_history(ticker_sym)
            
        if not df.empty:
            # Metrics Logic
            close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            delta = close - prev_close
            pct_change = (delta / prev_close) * 100
            color = "#10b981" if delta >= 0 else "#ef4444"
            sign = "+" if delta >= 0 else ""
            
            # Key Statistics Row
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                st.markdown("<p style='color:#94a3b8; margin:0; font-size:0.9rem;'>Current Price</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:0;'>${close:,.2f} <span style='color:{color}; font-size:1.2rem;'>{sign}{delta:,.2f} ({sign}{pct_change:.2f}%)</span></h2>", unsafe_allow_html=True)
            with m2:
                mkt_cap = info.get('marketCap', 'N/A')
                mkt_cap_fmt = f"${mkt_cap / 1e9:.2f}B" if isinstance(mkt_cap, (int, float)) else "N/A"
                st.markdown("<p style='color:#94a3b8; margin:0; font-size:0.9rem;'>Market Cap</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:0;'>{mkt_cap_fmt}</h2>", unsafe_allow_html=True)
            with m3:
                vol = info.get('volume', df['Volume'].iloc[-1])
                vol_fmt = f"{vol / 1e6:.2f}M" if vol else "N/A"
                st.markdown("<p style='color:#94a3b8; margin:0; font-size:0.9rem;'>Volume</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:0;'>{vol_fmt}</h2>", unsafe_allow_html=True)
            with m4:
                pe = info.get('trailingPE', 'N/A')
                pe_fmt = f"{pe:.2f}" if isinstance(pe, (int, float)) else "N/A"
                st.markdown("<p style='color:#94a3b8; margin:0; font-size:0.9rem;'>P/E Ratio</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:0;'>{pe_fmt}</h2>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Tabs for Chart vs News
            tab1, tab2 = st.tabs(["📊 Technical Chart", "📰 News Flow"])
            
            with tab1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                chart_type = st.radio("Chart Type:",["Advanced Candlestick", "Line Chart"], horizontal=True, label_visibility="collapsed")
                
                if chart_type == "Advanced Candlestick":
                    # TradingView Style Chart using Plotly Subplots
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
                    
                    # Candlestick
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
                    # Moving Averages
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#38bdf8', width=1.5), name="20 SMA"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#f59e0b', width=1.5), name="50 SMA"), row=1, col=1)
                    
                    # Volume
                    colors = ['#10b981' if row['Close'] - row['Open'] >= 0 else '#ef4444' for index, row in df.iterrows()]
                    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)
                    
                    fig.update_layout(
                        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=10, b=0), height=600, showlegend=False,
                        xaxis_rangeslider_visible=False
                    )
                    fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)', title_text="Price", row=1, col=1)
                    fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)', title_text="Volume", row=2, col=1)
                    fig.update_xaxes(gridcolor='rgba(255,255,255,0.05)')
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.line_chart(df['Close'], color="#38bdf8", height=500)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with tab2:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                if news:
                    for article in news[:5]: # Show top 5 recent articles
                        pub_time = datetime.fromtimestamp(article.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M')
                        st.markdown(f"""
                            <div style="padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px;">
                                <div style="color: #38bdf8; font-size: 0.8rem; margin-bottom: 5px;">{article.get('publisher', 'News')} • {pub_time}</div>
                                <a href="{article.get('link', '#')}" target="_blank" style="color: white; text-decoration: none; font-size: 1.1rem; font-weight: 600;">{article.get('title', 'No Title')}</a>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No recent news feed available for this asset.")
                st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.error(f"Failed to fetch market data for {ticker_sym}. Please verify the ticker symbol.")
