import streamlit as st
import requests
import pandas as pd
import time

# --- 1. SETTINGS & CUSTOM CSS ---
st.set_page_config(page_title="Titan Forensics", page_icon="🦅", layout="wide")

# Injecting Custom CSS for a "Trading Terminal" look
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    h1 {
        color: #00f2fe;
        font-family: 'Courier New', Courier, monospace;
        text-shadow: 0px 0px 10px rgba(0, 242, 254, 0.3);
    }
    h3 {
        color: #a0aec0;
    }
    .stButton>button {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0px 0px 15px rgba(0, 198, 255, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA FETCHING (WITH SMART CACHING) ---
# This saves the data for 1 hour so you don't burn through your API limits!
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
            return df.sort_index().tail(60) # Return the last 60 days
        return None
    except Exception as e:
        return None

# --- 3. IMMEDIATE UI ---
st.title("🦅 TITAN MACRO-FORENSICS")
st.success("Infrastructure Handshake: SECURE")

st.markdown("""
### System Status: **ONLINE**
The forensic suite is active. Protected by memory caching protocols.
""")

# --- 4. THE LOGIC ---
if st.button("🚀 EXECUTE INSTITUTIONAL ANALYSIS", use_container_width=True):
    API_KEY = "ip5kXCek8q0geIxaoNf8HtTbnS3Nh6Go"
    tickers = ['AAPL', 'MSFT']
    
    with st.spinner("Accessing Alpha Vantage Terminals..."):
        all_df = []
        for i, ticker in enumerate(tickers):
            df = fetch_ticker_data(ticker, API_KEY)
            if df is not None:
                all_df.append(df)
            else:
                st.error(f"Failed to fetch data for {ticker}. API limit may be reached.")
            
            # Prevent rapid-fire API hits if it's not cached yet
            if i < len(tickers) - 1:
                time.sleep(2) 
        
        if all_df:
            master_df = pd.concat(all_df)
            for ticker in tickers:
                st.divider()
                st.subheader(f"📊 {ticker} Profile")
                t_df = master_df[master_df['Ticker'] == ticker]
                
                if not t_df.empty:
                    c1, c2 = st.columns([2, 1])
                    with c1: 
                        st.markdown("**Price Action (Close)**")
                        st.line_chart(t_df['Close'], color="#00f2fe")
                    with c2: 
                        st.markdown("**Institutional Volume**")
                        st.bar_chart(t_df['Volume'], color="#ff4b4b")
