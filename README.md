# ⚛ TITAN MACRO-FORENSICS TERMINAL

**Titan V13** is a high-performance, institutional-grade financial monitoring dashboard built for rapid asset analysis. This version features a secure **Supabase** backend, persistent **PostgreSQL** storage, and real-time **Google S2 Telemetry** for corporate identity.

---

## 🚀 LIVE DEPLOYMENT
**Access the terminal here:** [https://titan-forensics-zeros-codexd.streamlit.app/]

---

## 🛠 CORE ARCHITECTURE
- **Frontend:** [Streamlit](https://streamlit.io/) (Python-based reactive UI)
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL for persistent user watchlists)
- **Authentication:** [Supabase Auth](https://supabase.com/auth) (Email/Password encrypted gateway)
- **Security:** Browser-side cookies via `streamlit-cookies-controller` for persistent sessions.
- **Data Engine:** `yfinance` with a specialized caching layer to prevent API rate-limiting.
- **Identity API:** Dynamic metadata scraping + Google S2 Favicon API for real-time corporate logos.

---

## ✨ KEY FEATURES
* **Secure Gateway:** Institutional-style login/signup flow to protect user data.
* **Persistent Watchlists:** Your assets follow you. Changes are saved to the cloud instantly.
* **Dynamic Metadata:** Automatically detects company names and logos for any global ticker (including `.NS` for NSE stocks).
* **Dual-Matrix Visualization:** Toggle between high-speed line charts and professional Candlestick charts for deep price action analysis.
* **Command Node UI:** Optimized dark-mode terminal aesthetic with custom CSS for high-contrast visibility.

---

## ⚙️ INSTALLATION & SETUP

To run this terminal locally:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/titan-forensics.git](https://github.com/YOUR_USERNAME/titan-forensics.git)
   cd titan-forensics

2. **Install Dependencies:**
```bash
pip install -r requirements.txt

3. **Configure Secrets:**
Create a .streamlit/secrets.toml file and add your Supabase credentials:
```bash
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_anon_key"

4. **Run the App:**
```bash
streamlit run main.py

## 🏗 SYSTEM EVOLUTION
V1-V5: Initial UI prototyping and logic testing.

V6-V10: Migration to Supabase and implementation of encrypted Auth.

V11-V13: Visual overhaul, logo telemetry integration, and persistent browser sessions.

## ⚖️ DISCLAIMER 
This tool is for educational and forensic analysis purposes only. All financial data is retrieved from public sources and may be delayed. Use for active trading at your own risk.
