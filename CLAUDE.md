# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Brazilian stock market quotation dashboard built with Streamlit. Displays 2025 YTD price history, candlestick charts, and key metrics for a hardcoded set of B3-listed tickers.

## Running the App

```bash
pip install -r acoes-2025/requirements.txt
streamlit run acoes-2025/app.py
```

There is no build system, test suite, or linter configured.

## Architecture

The entire application lives in `acoes-2025/app.py` (~79 lines). All logic — data fetching, caching, metric calculation, and rendering — is in that single file.

**Data flow:**
1. User picks a stock via sidebar radio (`ACOES` dict maps display name → Yahoo Finance ticker)
2. `carregar_dados(ticker)` fetches OHLCV data via `yfinance.download()` from 2025-01-01 to today; result is cached for 300 s with `@st.cache_data(ttl=300)`
3. Metrics (current price, daily change, 2025 high/low) are derived directly from the DataFrame
4. A Plotly candlestick chart and a formatted table of the last 10 sessions are rendered

**Supported tickers** (defined in `ACOES`):
- Petrobras → `PETR4.SA`
- Itaú → `ITUB4.SA`
- Vale → `VALE3.SA`

**Key libraries:** `streamlit`, `yfinance`, `plotly`, `pandas`

## Adding a New Stock

Add an entry to the `ACOES` dict at the top of `app.py`:

```python
ACOES = {
    ...,
    "Display Name (TICK4)": "TICK4.SA",
}
```

Yahoo Finance tickers for B3 stocks use the `.SA` suffix.
