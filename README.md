# 🪙 Crypto Memecoin Intelligence Platform

A comprehensive intelligence toolkit for profiling, analyzing, and scoring newly launched crypto tokens and their associated digital presence. This platform is modular, extensible, and designed for crypto communities, analysts, and investors.

---

## 🚀 Branch Overview

| Branch   | Purpose |
|----------|---------|
| `main`   | 🔍 **Token Profiling** – Extracts and analyzes core token metadata such as name, symbol, decimals, holders, and contract activity from blockchain APIs. |
| `main1`  | 📈 **Market Analysis** – Tracks real-time market data using sources like DEX Screener, computes liquidity trends, price volatility, and holder concentration metrics. |
| `main2`  | 🌐 **Website Intelligence** – Performs WHOIS, SSL, registrar, and Twitter intelligence with modular scoring. Combines Domain & Twitter credibility with deduction reasoning and total score (out of 100). |

---

## 🧱 Features

- **Modular Architecture**: Independent evaluators for each analysis component (domain, Twitter, token, market).
- **Scoring System**: Objective scoring for website trust, Twitter presence, market legitimacy, and token structure.
- **Streamlit Frontend**: User-friendly visual output for all data points and assessments.
- **Automation-Ready**: Cleanly separated backend logic for easy integration into bots, scripts, or dashboards.

---

## 📁 Directory Highlights

```
Blockchain_Scam_Analyzer/
├── .env
├── .gitignore
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── components/
│   ├── token_profile.py
│   ├── market_analysis.py
│   └── website_intelligence.py
│
├── utils/
│   ├── api.py
│   ├── parser.py
│   └── twitter_scrapper.py
│
└── .git/
```

## 🚀 How to Run

```bash
# Clone the repository
git clone https://github.com/Hyper-Baraaq/Crypto_Memecoin.git
cd Crypto_Memecoin

# Checkout the main2 branch
git checkout main2

# Create and activate virtual environment (optional)
python -m venv myenv
source myenv/bin/activate   # or .\myenv\Scripts\activate on Windows

# Install required packages
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
