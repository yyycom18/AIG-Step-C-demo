# HY-IG Spread Indicator Analysis

**Repository:** [https://github.com/yyycom18/AIG-Step-C-demo](https://github.com/yyycom18/AIG-Step-C-demo)

## Overview
This project analyzes the relationship between the HY-IG spread (High Yield minus Investment Grade Option-Adjusted Spread) and S&P 500 ETF (SPY) performance. The analysis follows the Time Series Relationship Analysis Framework to provide fundamental and technical insights for monthly/quarterly investment planning.

## Data Sources
- **HY-IG Spread**: FRED Series BAMLH0A0HYM2 (High Yield OAS) and BAMLC0A0CM (Investment Grade OAS)
  - Difference = HY - IG spread
- **S&P 500 ETF**: SPY from yfinance library

## Analysis Framework
The analysis follows the Time Series Relationship Analysis Framework with these sections:
1. **Qualitative Analysis** - Understanding the indicator
2. **Data Preparation** - Load, align, and create derivatives
3. **Correlation Analysis** - Level, change, and direction correlations
4. **Lead-Lag Analysis** - Identify leading/lagging relationships
5. **Causality Testing** - Granger causality tests
6. **Predictive Modeling** - ML models with lagged features
7. **Regime Analysis** - Performance by spread regime
8. **Visualizations** - Time series, scatter plots, regime charts
9. **Investment Strategy** - Backtested strategy implementation (1993-present)

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set FRED API Key
The project uses the same FRED API key as Project02. If not set:
```bash
# Windows PowerShell
$env:FRED_API_KEY="your_api_key_here"

# Or use the helper script from Project02
cd ../Project02
python set_fred_key.py
```

Get a free API key from: https://fred.stlouisfed.org/docs/api/api_key.html

### 3. Fetch Data
```bash
python fetch_data.py
```

This creates:
- `data/hyig_spy_daily.csv` - Daily data
- `data/hyig_spy_monthly.csv` - Monthly data
- `data/hyig_spy_quarterly.csv` - Quarterly data
- `data/hyig_data.json` - JSON data for web interface

### 4. Run Analysis
```bash
python analysis.py
```

### 5. Run Strategy Backtest
```bash
python strategy_backtest.py
```

### 6. Run the Website (Local)
```bash
python run_server.py
```

Then open browser to: http://localhost:8001

### 7. Deploy to Streamlit Cloud (Share with Team)
See `DEPLOY_STREAMLIT.md` for detailed instructions.

Quick steps:
1. Sign up at https://streamlit.io/cloud
2. Connect your GitHub account
3. Deploy from repository: `yyycom18/AIG-Step-C-demo`
4. Main file: `streamlit_app.py`
5. Share the URL with your teammates!

## Project Structure
```
Project03/
├── data/                  # Data files (CSV, JSON)
├── analysis.py           # Main analysis script
├── fetch_data.py         # Data fetching from FRED and yfinance
├── strategy_backtest.py  # Investment strategy backtesting
├── index03.html          # Main website (includes interactive visualizations)
├── run_server.py         # Local HTTP server
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Key Features
- Comprehensive time series relationship analysis
- Interactive visualizations
- Backtested investment strategy with performance metrics
- Monthly/quarterly investment plan framework
- Historical analysis from 1993 to present

## Quick Start Guide

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure FRED API key is set** (uses same key as Project02):
   ```bash
   # Check if already set
   echo $env:FRED_API_KEY  # PowerShell
   # If not set, use Project02 helper script
   cd ../Project02
   python set_fred_key.py
   ```

3. **Fetch data:**
   ```bash
   cd Project03
   python fetch_data.py
   ```

4. **Run analysis:**
   ```bash
   python analysis.py
   ```

5. **Run strategy backtest:**
   ```bash
   python strategy_backtest.py
   ```

6. **Start the website:**
   ```bash
   python run_server.py
   ```

7. **Open browser to:** http://localhost:8001

## Notes

## HY-IG Spread Percentile Calculation Strategy _(Updated: 2026-01-18)_

- **Percentile Calculation Window:**
  - 5 years (60 months) using a rolling window.
- **How it works:**
  - For each month, the algorithm examines the previous 60 months of HY-IG spread data.
  - Computes percentiles P25, P50, P75, P90 over this window.
  - Minimum 12 months (1 year) of data is required before percentiles can be calculated.
  - These percentiles define "regimes" for analysis and signal assignment.
- **Example:**
  - For December 2024: percentiles are based on data from January 2020 to December 2024 (inclusive).
  - For January 2025: percentiles use data from February 2020 to January 2025 (inclusive).
- **Purpose:**
  - The percentiles are recalculated every month using the latest 5-year period, so they adapt to recent market trends and conditions.

_Summary: Percentile thresholds for regimes/signals always use the most recent 5 years (rolling 60 months) of data up to the analysis point._

- Analysis period: 1993-present (HY-IG spread data availability)
- The spread is calculated as HY OAS - IG OAS
- Strategy backtesting includes return%, win rate, and implementation timing
- The website requires data files from steps 3-5 to display all sections