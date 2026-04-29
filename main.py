import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Titan Forensics", layout="wide")

st.title("🦅 TITAN MACRO-FORENSICS")
st.success("Infrastructure Handshake: SECURE")

st.markdown("""
### System Status: **ONLINE**
The forensic suite is active. 
""")

if st.button("🚀 EXECUTE INSTITUTIONAL ANALYSIS", use_container_width=True):
    API_KEY = "ip5kXCek8q0geIxaoNf8HtTbnS3Nh6Go"
    tickers = ['AAPL', 'MSFT']
    
    with st.spinner("Accessing Alpha Vantage Terminals..."):
        all_df = []
        for ticker in tickers:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}"
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
                    all_df.append(df.sort_index().tail(60))
                    if ticker != tickers[-1]:
                        time.sleep(15) 
            except Exception as e:
                st.error(f"Error: {e}")
        
        if all_df:
            master_df = pd.concat(all_df)
            for ticker in tickers:
                st.divider()
                st.subheader(f"📊 {ticker} Profile")
                t_df = master_df[master_df['Ticker'] == ticker]
                c1, c2 = st.columns([2, 1])
                with c1: st.line_chart(t_df['Close'], color="#1f77b4")
                with c2: st.bar_chart(t_df['Volume'], color="#d62728")
