"""
Data fetching script for HY-IG Spread analysis
Fetches High Yield and Investment Grade OAS from FRED, calculates spread, and fetches SPY from yfinance
"""
import os
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf
from fredapi import Fred

# Configuration
START_DATE = "1993-01-01"  # HY-IG spread data starts around 1993
# END_DATE will be set to today's date to get latest data
OUTPUT_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_spy_data():
    """Fetch S&P 500 ETF (SPY) data from yfinance"""
    print("Fetching SPY data...")
    ticker = yf.Ticker("SPY")
    # Fetch data up to latest available date (no end date specified)
    hist = ticker.history(start=START_DATE)
    spy = hist["Close"].dropna()
    spy.name = "SPY"
    print(f"  SPY date range: {spy.index.min()} to {spy.index.max()}")
    print(f"  SPY records: {len(spy)}")
    return spy


def fetch_hyig_spread():
    """Fetch HY-IG spread data from FRED"""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        print("\n" + "=" * 60)
        print("ERROR: FRED_API_KEY environment variable not set")
        print("=" * 60)
        print("\nTo set your FRED API key:")
        print("1. Get a free API key from: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Run this helper script from Project02: python ../Project02/set_fred_key.py")
        print("   OR set it manually:")
        print("   PowerShell: $env:FRED_API_KEY='your_key_here'")
        print("   CMD: set FRED_API_KEY=your_key_here")
        print("\n" + "=" * 60)
        raise ValueError("FRED_API_KEY environment variable not set.")
    
    try:
        fred = Fred(api_key=api_key)
    except ValueError as e:
        print(f"ERROR: Invalid FRED API key: {e}")
        raise
    
    # Fetch High Yield OAS
    print("Fetching High Yield OAS (BAMLH0A0HYM2)...")
    try:
        # Fetch data up to latest available date (no observation_end specified)
        hy_oas = fred.get_series("BAMLH0A0HYM2", 
                                 observation_start=START_DATE)
        
        # Validate data
        if len(hy_oas) == 0:
            raise ValueError("No data returned for HY OAS (BAMLH0A0HYM2). "
                           "Series may not exist or date range has no data.")
        
        hy_oas.name = "HY_OAS"
        print(f"  HY OAS date range: {hy_oas.index.min()} to {hy_oas.index.max()}")
        print(f"  HY OAS records: {len(hy_oas)}")
        
        # Check data quality
        missing_pct = hy_oas.isna().sum() / len(hy_oas) * 100
        if missing_pct > 10:
            print(f"  WARNING: {missing_pct:.1f}% missing values in HY OAS data")
            
    except (ValueError, KeyError, ConnectionError) as e:
        print(f"  ERROR fetching HY OAS (BAMLH0A0HYM2): {str(e)}")
        raise ValueError(f"Could not fetch HY OAS data. Check FRED series BAMLH0A0HYM2.\n"
                        f"Details: {str(e)}")
    except Exception as e:
        print(f"  UNEXPECTED ERROR fetching HY OAS: {type(e).__name__}: {str(e)}")
        raise
    
    # Fetch Investment Grade OAS
    print("Fetching Investment Grade OAS (BAMLC0A0CM)...")
    try:
        # Fetch data up to latest available date (no observation_end specified)
        ig_oas = fred.get_series("BAMLC0A0CM", 
                                 observation_start=START_DATE)
        
        # Validate data
        if len(ig_oas) == 0:
            raise ValueError("No data returned for IG OAS (BAMLC0A0CM). "
                           "Series may not exist or date range has no data.")
        
        ig_oas.name = "IG_OAS"
        print(f"  IG OAS date range: {ig_oas.index.min()} to {ig_oas.index.max()}")
        print(f"  IG OAS records: {len(ig_oas)}")
        
        # Check data quality
        missing_pct = ig_oas.isna().sum() / len(ig_oas) * 100
        if missing_pct > 10:
            print(f"  WARNING: {missing_pct:.1f}% missing values in IG OAS data")
            
    except (ValueError, KeyError, ConnectionError) as e:
        print(f"  ERROR fetching IG OAS (BAMLC0A0CM): {str(e)}")
        raise ValueError(f"Could not fetch IG OAS data. Check FRED series BAMLC0A0CM.\n"
                        f"Details: {str(e)}")
    except Exception as e:
        print(f"  UNEXPECTED ERROR fetching IG OAS: {type(e).__name__}: {str(e)}")
        raise
    
    # Calculate HY-IG Spread (HY - IG)
    print("Calculating HY-IG Spread...")
    df_temp = pd.DataFrame({"HY_OAS": hy_oas, "IG_OAS": ig_oas})
    df_temp = df_temp.sort_index()
    df_temp["HY_IG_Spread"] = df_temp["HY_OAS"] - df_temp["IG_OAS"]
    spread = df_temp["HY_IG_Spread"].dropna()
    spread.name = "HY_IG_Spread"
    
    print(f"  HY-IG Spread date range: {spread.index.min()} to {spread.index.max()}")
    print(f"  HY-IG Spread records: {len(spread)}")
    print(f"  Spread statistics:")
    print(f"    Mean: {spread.mean():.2f} bps")
    print(f"    Std: {spread.std():.2f} bps")
    print(f"    Min: {spread.min():.2f} bps")
    print(f"    Max: {spread.max():.2f} bps")
    print(f"    Missing: {spread.isna().sum()}")
    
    return df_temp["HY_OAS"], df_temp["IG_OAS"], spread


def fetch_fed_funds_rate():
    """Fetch Federal Funds Rate from FRED"""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        print("WARNING: FRED_API_KEY not set, skipping Fed Funds Rate")
        return None
    
    try:
        fred = Fred(api_key=api_key)
        print("Fetching Federal Funds Rate (FEDFUNDS)...")
        # Fetch data up to latest available date (no observation_end specified)
        fed_funds = fred.get_series("FEDFUNDS",
                                    observation_start=START_DATE)
        
        if len(fed_funds) == 0:
            print("  WARNING: No Fed Funds Rate data returned")
            return None
        
        fed_funds.name = "FEDFUNDS"
        print(f"  Fed Funds Rate date range: {fed_funds.index.min()} to {fed_funds.index.max()}")
        print(f"  Fed Funds Rate records: {len(fed_funds)}")
        print(f"  Rate range: {fed_funds.min():.2f}% to {fed_funds.max():.2f}%")
        return fed_funds
        
    except Exception as e:
        print(f"  WARNING: Could not fetch Fed Funds Rate: {str(e)}")
        return None


def prepare_data():
    """Fetch and combine all data"""
    hy_oas, ig_oas, spread = fetch_hyig_spread()
    spy = fetch_spy_data()
    fed_funds = fetch_fed_funds_rate()
    
    # Normalize timezones - remove timezone info from SPY to match FRED data
    if spy.index.tz is not None:
        spy.index = spy.index.tz_localize(None)
        print("  Normalized SPY timezone to match FRED data")
    
    # Combine into DataFrame with common date index
    all_dates = hy_oas.index.union(ig_oas.index).union(spread.index).union(spy.index)
    if fed_funds is not None:
        all_dates = all_dates.union(fed_funds.index)
    
    df = pd.DataFrame(index=all_dates)
    df["HY_OAS"] = hy_oas
    df["IG_OAS"] = ig_oas
    df["HY_IG_Spread"] = spread
    df["SPY"] = spy
    if fed_funds is not None:
        df["FEDFUNDS"] = fed_funds
    
    # Sort and forward fill missing values (limited)
    df = df.sort_index()
    df = df.ffill(limit=5)  # Forward fill up to 5 days for missing values
    
    # Drop rows where essential data is missing
    df = df.dropna(subset=["HY_IG_Spread", "SPY"])
    
    # Calculate monthly data
    df_monthly = df.resample("ME").last()
    df_monthly["SPY_Returns"] = df_monthly["SPY"].pct_change() * 100
    if fed_funds is not None:
        # Forward fill Fed Funds Rate for monthly data
        df_monthly["FEDFUNDS"] = df_monthly["FEDFUNDS"].ffill()
    
    # Calculate quarterly data
    df_quarterly = df.resample("QE").last()
    df_quarterly["SPY_Returns"] = df_quarterly["SPY"].pct_change() * 100
    if fed_funds is not None:
        df_quarterly["FEDFUNDS"] = df_quarterly["FEDFUNDS"].ffill()
    
    # Save data
    df.to_csv(OUTPUT_DIR / "hyig_spy_daily.csv")
    df_monthly.to_csv(OUTPUT_DIR / "hyig_spy_monthly.csv")
    df_quarterly.to_csv(OUTPUT_DIR / "hyig_spy_quarterly.csv")
    
    # Create JSON for web interface
    data_json = {
        "metadata": {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "date_range": {
                "start": str(df.index.min()),
                "end": str(df.index.max())
            },
            "total_records": len(df)
        },
        "daily": {
            "dates": df.index.strftime("%Y-%m-%d").tolist(),
            "hy_oas": df["HY_OAS"].fillna("null").tolist(),
            "ig_oas": df["IG_OAS"].fillna("null").tolist(),
            "hy_ig_spread": df["HY_IG_Spread"].fillna("null").tolist(),
            "spy": df["SPY"].fillna("null").tolist(),
            "fedfunds": df["FEDFUNDS"].fillna("null").tolist() if "FEDFUNDS" in df.columns else ["null"] * len(df)
        },
        "monthly": {
            "dates": df_monthly.index.strftime("%Y-%m-%d").tolist(),
            "hy_oas": df_monthly["HY_OAS"].fillna("null").tolist(),
            "ig_oas": df_monthly["IG_OAS"].fillna("null").tolist(),
            "hy_ig_spread": df_monthly["HY_IG_Spread"].fillna("null").tolist(),
            "spy": df_monthly["SPY"].fillna("null").tolist(),
            "spy_returns": df_monthly["SPY_Returns"].fillna("null").tolist(),
            "fedfunds": df_monthly["FEDFUNDS"].fillna("null").tolist() if "FEDFUNDS" in df_monthly.columns else ["null"] * len(df_monthly)
        },
        "quarterly": {
            "dates": df_quarterly.index.strftime("%Y-%m-%d").tolist(),
            "hy_oas": df_quarterly["HY_OAS"].fillna("null").tolist(),
            "ig_oas": df_quarterly["IG_OAS"].fillna("null").tolist(),
            "hy_ig_spread": df_quarterly["HY_IG_Spread"].fillna("null").tolist(),
            "spy": df_quarterly["SPY"].fillna("null").tolist(),
            "spy_returns": df_quarterly["SPY_Returns"].fillna("null").tolist()
        },
        "stats": {
            "spread_mean": float(df["HY_IG_Spread"].mean()),
            "spread_std": float(df["HY_IG_Spread"].std()),
            "spread_min": float(df["HY_IG_Spread"].min()),
            "spread_max": float(df["HY_IG_Spread"].max()),
            "spread_p25": float(df["HY_IG_Spread"].quantile(0.25)),
            "spread_p50": float(df["HY_IG_Spread"].quantile(0.50)),
            "spread_p75": float(df["HY_IG_Spread"].quantile(0.75)),
            "spread_p90": float(df["HY_IG_Spread"].quantile(0.90))
        }
    }
    
    with open(OUTPUT_DIR / "hyig_data.json", "w") as f:
        json.dump(data_json, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Data saved to {OUTPUT_DIR}")
    print(f"{'='*60}")
    print(f"Final Date Range: {df.index.min()} to {df.index.max()}")
    print(f"Total daily records: {len(df)}")
    print(f"Total monthly records: {len(df_monthly)}")
    print(f"Total quarterly records: {len(df_quarterly)}")
    print(f"\nData Coverage:")
    print(f"  HY_OAS: {df['HY_OAS'].notna().sum()}/{len(df)} records ({df['HY_OAS'].notna().sum()/len(df)*100:.1f}%)")
    print(f"  IG_OAS: {df['IG_OAS'].notna().sum()}/{len(df)} records ({df['IG_OAS'].notna().sum()/len(df)*100:.1f}%)")
    print(f"  HY_IG_Spread: {df['HY_IG_Spread'].notna().sum()}/{len(df)} records ({df['HY_IG_Spread'].notna().sum()/len(df)*100:.1f}%)")
    print(f"  SPY: {df['SPY'].notna().sum()}/{len(df)} records ({df['SPY'].notna().sum()/len(df)*100:.1f}%)")
    if "FEDFUNDS" in df.columns:
        print(f"  FEDFUNDS: {df['FEDFUNDS'].notna().sum()}/{len(df)} records ({df['FEDFUNDS'].notna().sum()/len(df)*100:.1f}%)")
    
    return df, df_monthly, df_quarterly


if __name__ == "__main__":
    prepare_data()
