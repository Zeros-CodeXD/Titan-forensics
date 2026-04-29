# 🦅 Titan Macro-Forensics 

**Live Dashboard:** [Launch Titan Forensics](https://titan-forensics-zeros-codexd.streamlit.app/)

## Overview
Titan Macro-Forensics is a real-time, lightweight financial dashboard designed to track institutional trade volume and price action divergence. By pulling direct market data through the Alpha Vantage API, it visualizes immediate trends for major equities (currently tracking AAPL and MSFT).

## Features
* **Live API Integration:** Fetches up-to-date daily time series data via Alpha Vantage.
* **Volume/Price Divergence:** Side-by-side comparative charting for closing prices and trading volume to spot institutional accumulation or distribution.
* **Smart Caching:** Built-in data caching using `@st.cache_data` to minimize redundant API calls and protect rate limits.
* **Custom Terminal UI:** Injected CSS to simulate a high-contrast, professional trading terminal environment.

## Tech Stack
* **Language:** Python 3.11
* **Framework:** Streamlit (UI & Server)
* **Data Processing:** Pandas
* **API Routing:** Requests
* **Deployment:** Streamlit Community Cloud

## Infrastructure Note
This application was originally engineered to bypass restrictive, predefined enterprise cloud configurations. It utilizes a container-agnostic architecture, allowing it to be deployed instantly from a raw repository to any standard Python environment without relying on proprietary cloud terminal bootloaders.
