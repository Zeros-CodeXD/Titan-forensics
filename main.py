import streamlit as st
import requests
import pandas as pd
import time

# --- 1. SETTINGS & HIGH-FIDELITY CSS ---
st.set_page_config(page_title="Titan Forensics", page_icon="🦅", layout="wide")

st.markdown("""
    <style>
    /* Global Dark Theme */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    /* Glowing Headers */
    h1, h2, h3 {
        color: #38bdf8;
        font-family: 'Courier New', Courier, monospace;
        letter-spacing: 1px;
    }
    h1 {
        text-shadow: 0px 0px 15px rgba(56, 189, 248, 0.4);
        border-bottom: 1px solid #1e293b;
        padding-bottom: 10px;
    }
    /* Sleek Execution Button */
    .stButton>button {
        background: linear-gradient(90deg, #38bdf8 0%, #3b82f6 100%);
        color: #ffffff;
        border: none;
        border-radius: 6px;
        font-weight: 800;
        letter-spacing: 2px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0px 4px 15px rgba(59, 130, 246, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 6px 20px rgba(59, 130, 246, 0.6);
    }
    /* Metric Card Styling */
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE (CACHED) ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ticker_data(ticker, api_key):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={api_key}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={"4. close": "Close", "5. volume": "Volume"})
            df['Close'] = df['Close'].astype(float)
            df['Volume'] = df['Volume'].astype(float)
            df['Ticker'] = ticker
            return df.sort_index().tail(60) 
        return None
    except Exception as e:
        return None

# --- 3. DASHBOARD HEADER ---
st.title("🦅 TITAN MACRO-FORENSICS")

st.markdown("""
Welcome to the terminal. This system tracks institutional trade volume and price action divergence across major tech equities. 
*Status: Node Connected. Awaiting Execution command.*
""")

# --- 4. CORE LOGIC & UI RENDER ---
if st.button("🚀 EXECUTE INSTITUTIONAL ANALYSIS", use_container_width=True):
    API_KEY = "ip5kXCek8q0geIxaoNf8HtTbnS3Nh6Go"
    tickers = ['AAPL', 'MSFT'] # Add more stock symbols here if you want!
    
    with st.spinner("Establishing secure connection to Alpha Vantage..."):
        all_df = []
        for i, ticker in enumerate(tickers):
            df = fetch_ticker_data(ticker, API_KEY)
            if df is not None:
                all_df.append(df)
            else:
                st.error(f"Failed to fetch data for {ticker}. API limit reached.")
            
            if i < len(tickers) - 1:
                time.sleep(2) 
        
        if all_df:
            master_df = pd.concat(all_df)
            
            for ticker in tickers:
                st.write("---")
                t_df = master_df[master_df['Ticker'] == ticker]
                
                if not t_df.empty:
                    # Get the most recent day's data for the metric cards
                    latest_close = t_df['Close'].iloc[-1]
                    latest_vol = t_df['Volume'].iloc[-1]
                    prev_close = t_df['Close'].iloc[-2]
                    price_delta = latest_close - prev_close
                    
                    # Top Row: Clean Data Metrics
                    st.subheader(f"📊 {ticker} | Terminal Profile")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Latest Close Price", f"${latest_close:,.2f}", f"${price_delta:,.2f}")
                    with col2:
                        st.metric("Daily Trade Volume", f"{latest_vol:,.0f}")
                    with col3:
                        st.metric("Tracking Window", "60 Days")
                    
                    st.write("") # Spacer
                    
                    # Bottom Row: Visual Charts
                    c1, c2 = st.columns([2, 1])
                    with c1: 
                        st.markdown("**Price Action Trend**")
                        st.line_chart(t_df['Close'], color="#38bdf8") # Neon blue line
                    with c2: 
                        st.markdown("**Institutional Volume**")
                        st.bar_chart(t_df['Volume'], color="#3b82f6") # Deeper blue bars
