"""
Investment Strategy Backtesting for HY-IG Spread Indicator
Tests strategy implementation from 1993 to present with performance metrics
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Risk-free rate assumption (current 10-year treasury rate)
# Update quarterly based on current environment
RISK_FREE_RATE = 4.0  # Treasury rates as of Jan 2026

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Position sizing by regime
POSITION_SIZES = {
    'Low Spread (Buy)': 1.0,
    'Moderate-Low Spread': 0.75,
    'Moderate-High Spread': 0.50,
    'High Spread (Caution)': 0.25,
    'Very High Spread (Reduce Exposure)': 0.10,
    'Unknown': 0.50  # Default neutral
}


def load_data():
    """Load monthly data"""
    df_monthly = pd.read_csv(DATA_DIR / "hyig_spy_monthly.csv", index_col=0, parse_dates=True)
    return df_monthly


def identify_fed_rate_changes(df):
    """
    Identify periods when Fed Funds Rate increased or decreased
    Returns DataFrame with rate change information
    """
    if 'FEDFUNDS' not in df.columns or df['FEDFUNDS'].isna().all():
        print("  WARNING: Fed Funds Rate data not available")
        df['Fed_Rate_Change'] = 'No Change'
        df['Fed_Rate_Change_Type'] = 'none'
        return df
    
    df = df.copy()
    df['Fed_Rate_Change'] = 'No Change'
    df['Fed_Rate_Change_Type'] = 'none'
    
    # Forward fill Fed Funds Rate to handle missing values
    df['FEDFUNDS'] = df['FEDFUNDS'].ffill()
    
    # Calculate rate change (current - previous)
    df['Fed_Rate_Diff'] = df['FEDFUNDS'].diff()
    
    # Identify rate changes (using threshold to avoid noise)
    threshold = 0.05  # 5 basis points threshold
    
    # Rate increase
    df.loc[df['Fed_Rate_Diff'] > threshold, 'Fed_Rate_Change'] = 'Rate Increase'
    df.loc[df['Fed_Rate_Diff'] > threshold, 'Fed_Rate_Change_Type'] = 'increase'
    
    # Rate decrease
    df.loc[df['Fed_Rate_Diff'] < -threshold, 'Fed_Rate_Change'] = 'Rate Decrease'
    df.loc[df['Fed_Rate_Diff'] < -threshold, 'Fed_Rate_Change_Type'] = 'decrease'
    
    # Create periods (shapes for chart backgrounds)
    rate_periods = []
    current_period = None
    
    for idx, row in df.iterrows():
        if row['Fed_Rate_Change_Type'] != 'none':
            if current_period is None or current_period['type'] != row['Fed_Rate_Change_Type']:
                # End previous period if exists
                if current_period is not None:
                    current_period['end'] = str(idx)
                    rate_periods.append(current_period)
                
                # Start new period
                current_period = {
                    'type': row['Fed_Rate_Change_Type'],
                    'start': str(idx),
                    'end': None
                }
        elif current_period is not None:
            # End current period
            current_period['end'] = str(idx)
            rate_periods.append(current_period)
            current_period = None
    
    # Close final period if exists
    if current_period is not None:
        current_period['end'] = str(df.index[-1])
        rate_periods.append(current_period)
    
    return df, rate_periods


def calculate_spread_percentiles(df, window=60):
    """Calculate rolling percentiles for spread"""
    df['Spread_P25'] = df['HY_IG_Spread'].rolling(window=window, min_periods=12).quantile(0.25)
    df['Spread_P50'] = df['HY_IG_Spread'].rolling(window=window, min_periods=12).quantile(0.50)
    df['Spread_P75'] = df['HY_IG_Spread'].rolling(window=window, min_periods=12).quantile(0.75)
    df['Spread_P90'] = df['HY_IG_Spread'].rolling(window=window, min_periods=12).quantile(0.90)
    return df


def backtest_strategy(df, strategy_type='percentile_based'):
    """
    Backtest strategy based on HY-IG spread regimes
    
    Strategy logic:
    - Low Spread (≤P25): Full exposure (100% SPY)
    - Moderate-Low (P25-P50): 75% exposure
    - Moderate-High (P50-P75): 50% exposure
    - High Spread (P75-P90): 25% exposure
    - Very High Spread (>P90): 10% exposure (defensive)
    """
    df = df.copy()
    df = calculate_spread_percentiles(df)
    
    # Vectorized regime assignment (much faster!)
    conditions = [
        df['HY_IG_Spread'] <= df['Spread_P25'],
        (df['HY_IG_Spread'] > df['Spread_P25']) & (df['HY_IG_Spread'] <= df['Spread_P50']),
        (df['HY_IG_Spread'] > df['Spread_P50']) & (df['HY_IG_Spread'] <= df['Spread_P75']),
        (df['HY_IG_Spread'] > df['Spread_P75']) & (df['HY_IG_Spread'] <= df['Spread_P90']),
        df['HY_IG_Spread'] > df['Spread_P90'],
        df['HY_IG_Spread'].isna()  # Handle NaN
    ]
    
    choices = [
        'Low Spread (Buy)',
        'Moderate-Low Spread',
        'Moderate-High Spread',
        'High Spread (Caution)',
        'Very High Spread (Reduce Exposure)',
        'Unknown'
    ]
    
    # Use np.select for vectorized operation (O(1) instead of O(n))
    df['Regime'] = np.select(conditions, choices, default='Unknown')
    
    # Vectorized position sizing lookup
    df['Position_Size'] = df['Regime'].map(POSITION_SIZES).fillna(0.50)
    
    # Validate position sizes
    if df['Position_Size'].isna().any():
        print(f"  WARNING: {df['Position_Size'].isna().sum()} rows have invalid position sizes")
        df['Position_Size'] = df['Position_Size'].fillna(0.50)
    
    # Calculate strategy returns (position size * SPY return)
    df['Strategy_Return'] = df['Position_Size'] * df['SPY_Returns']
    df['Strategy_Return'] = df['Strategy_Return'].fillna(0)
    
    # Calculate cumulative returns
    df['SPY_Cumulative'] = (1 + df['SPY_Returns'] / 100).cumprod()
    df['Strategy_Cumulative'] = (1 + df['Strategy_Return'] / 100).cumprod()
    
    # Calculate drawdowns
    df['SPY_Drawdown'] = (df['SPY_Cumulative'] / df['SPY_Cumulative'].cummax() - 1) * 100
    df['Strategy_Drawdown'] = (df['Strategy_Cumulative'] / df['Strategy_Cumulative'].cummax() - 1) * 100
    
    return df


def calculate_performance_by_fed_periods(df):
    """
    Calculate performance metrics by Fed rate change periods
    Also calculates performance for Fed Funds Rate > 2.5% and < 2.5%
    """
    results = {}
    
    # Calculate by rate change type (increase, decrease, none)
    if 'Fed_Rate_Change_Type' in df.columns:
        for change_type in ['increase', 'decrease', 'none']:
            period_data = df[df['Fed_Rate_Change_Type'] == change_type].copy()
            
            if len(period_data) == 0:
                continue
            
            results[change_type] = calculate_period_metrics(period_data)
    
    # Calculate by Fed Funds Rate level (> 2.5% and < 2.5%)
    if 'FEDFUNDS' in df.columns:
        # High rate period (>= 2.5%)
        high_rate_data = df[df['FEDFUNDS'] >= 2.5].copy()
        if len(high_rate_data) > 0:
            results['rate_above_2.5'] = calculate_period_metrics(high_rate_data)
        
        # Low rate period (< 2.5%)
        low_rate_data = df[df['FEDFUNDS'] < 2.5].copy()
        if len(low_rate_data) > 0:
            results['rate_below_2.5'] = calculate_period_metrics(low_rate_data)
    
    return results


def calculate_period_metrics(period_data):
    """
    Helper function to calculate performance metrics for a given period
    """
    # Calculate metrics for this period
    period_returns = period_data['Strategy_Return'].dropna()
    spy_returns = period_data['SPY_Returns'].dropna()
    
    if len(period_returns) == 0:
        return {
            'n_months': 0,
            'strategy': {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0
            },
            'spy': {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0
            }
        }
    
    # Cumulative returns
    period_strategy_cum = (1 + period_returns / 100).cumprod()
    period_spy_cum = (1 + spy_returns / 100).cumprod()
    
    # Total return
    strategy_total = (period_strategy_cum.iloc[-1] / period_strategy_cum.iloc[0] - 1) * 100 if len(period_strategy_cum) > 0 else 0
    spy_total = (period_spy_cum.iloc[-1] / period_spy_cum.iloc[0] - 1) * 100 if len(period_spy_cum) > 0 else 0
    
    # Annualized return
    n_months = len(period_data)
    n_years = n_months / 12
    if n_years > 0:
        strategy_annualized = ((period_strategy_cum.iloc[-1] / period_strategy_cum.iloc[0]) ** (1/n_years) - 1) * 100 if len(period_strategy_cum) > 0 else 0
        spy_annualized = ((period_spy_cum.iloc[-1] / period_spy_cum.iloc[0]) ** (1/n_years) - 1) * 100 if len(period_spy_cum) > 0 else 0
    else:
        strategy_annualized = 0
        spy_annualized = 0
    
    # Volatility
    strategy_vol = period_returns.std() * np.sqrt(12) if len(period_returns) > 1 else 0
    spy_vol = spy_returns.std() * np.sqrt(12) if len(spy_returns) > 1 else 0
    
    # Sharpe ratio
    strategy_excess = strategy_annualized - RISK_FREE_RATE
    spy_excess = spy_annualized - RISK_FREE_RATE
    strategy_sharpe = strategy_excess / strategy_vol if strategy_vol > 0 else 0
    spy_sharpe = spy_excess / spy_vol if spy_vol > 0 else 0
    
    # Max drawdown
    strategy_dd = period_data['Strategy_Drawdown'].min() if 'Strategy_Drawdown' in period_data.columns else 0
    spy_dd = period_data['SPY_Drawdown'].min() if 'SPY_Drawdown' in period_data.columns else 0
    
    # Win rate
    strategy_win_rate = (period_returns > 0).sum() / len(period_returns) * 100 if len(period_returns) > 0 else 0
    spy_win_rate = (spy_returns > 0).sum() / len(spy_returns) * 100 if len(spy_returns) > 0 else 0
    
    return {
        'n_months': int(n_months),
        'strategy': {
            'total_return': float(strategy_total),
            'annualized_return': float(strategy_annualized),
            'volatility': float(strategy_vol),
            'sharpe_ratio': float(strategy_sharpe),
            'max_drawdown': float(strategy_dd),
            'win_rate': float(strategy_win_rate)
        },
        'spy': {
            'total_return': float(spy_total),
            'annualized_return': float(spy_annualized),
            'volatility': float(spy_vol),
            'sharpe_ratio': float(spy_sharpe),
            'max_drawdown': float(spy_dd),
            'win_rate': float(spy_win_rate)
        }
    }


def generate_current_strategy_review(df, lookback_months=12):
    """
    Generate current strategy review for the past N months
    Returns list of regime/action records with dates
    """
    from datetime import datetime, timedelta
    
    # Get most recent data
    cutoff_date = df.index.max() - pd.DateOffset(months=lookback_months)
    recent_df = df[df.index >= cutoff_date].copy()
    
    if len(recent_df) == 0:
        return []
    
    # Identify position changes (when regime changes)
    recent_df['Position_Change'] = recent_df['Regime'].ne(recent_df['Regime'].shift())
    recent_df['Position_Size_Change'] = recent_df['Position_Size'].ne(recent_df['Position_Size'].shift())
    
    review_records = []
    
    for idx, row in recent_df.iterrows():
        # Check if this is a position change
        is_action = row['Position_Change'] or row['Position_Size_Change']
        
        # Determine action type
        action = None
        if is_action:
            prev_size = recent_df.loc[recent_df.index < idx, 'Position_Size'].iloc[-1] if len(recent_df[recent_df.index < idx]) > 0 else row['Position_Size']
            if row['Position_Size'] > prev_size:
                action = 'Increase Position'
            elif row['Position_Size'] < prev_size:
                action = 'Decrease Position'
            else:
                action = 'Regime Change'
        
        record = {
            'date': str(idx),
            'regime': str(row['Regime']),
            'spread': float(row['HY_IG_Spread']) if pd.notna(row['HY_IG_Spread']) else None,
            'position_size': float(row['Position_Size']) if pd.notna(row['Position_Size']) else None,
            'spy_return': float(row['SPY_Returns']) if pd.notna(row['SPY_Returns']) else None,
            'strategy_return': float(row['Strategy_Return']) if pd.notna(row['Strategy_Return']) else None,
            'has_action': bool(is_action),
            'action': action
        }
        
        review_records.append(record)
    
    return review_records


def calculate_performance_metrics(df, risk_free_rate=RISK_FREE_RATE):
    """
    Calculate performance metrics
    
    Args:
        df: DataFrame with SPY and strategy returns
        risk_free_rate: Annual risk-free rate (%)
    """
    # Remove NaN rows
    df_clean = df[df['SPY_Returns'].notna() & df['Strategy_Return'].notna()].copy()
    
    if len(df_clean) == 0:
        print("ERROR: No valid data for metrics calculation")
        return None
    
    # Validate data
    if len(df_clean) < 12:
        print(f"WARNING: Only {len(df_clean)} months of data (need ≥12 for annual metrics)")
    
    # Total return
    spy_total_return = (df_clean['SPY_Cumulative'].iloc[-1] / df_clean['SPY_Cumulative'].iloc[0] - 1) * 100
    strategy_total_return = (df_clean['Strategy_Cumulative'].iloc[-1] / df_clean['Strategy_Cumulative'].iloc[0] - 1) * 100
    
    # Annualized return (assuming monthly data)
    n_years = (df_clean.index[-1] - df_clean.index[0]).days / 365.25
    spy_annualized = ((df_clean['SPY_Cumulative'].iloc[-1] / df_clean['SPY_Cumulative'].iloc[0]) ** (1/n_years) - 1) * 100
    strategy_annualized = ((df_clean['Strategy_Cumulative'].iloc[-1] / df_clean['Strategy_Cumulative'].iloc[0]) ** (1/n_years) - 1) * 100
    
    # Volatility (annualized)
    spy_vol = df_clean['SPY_Returns'].std() * np.sqrt(12)
    strategy_vol = df_clean['Strategy_Return'].std() * np.sqrt(12)
    
    # Sharpe ratio (excess return / volatility)
    spy_excess_return = spy_annualized - risk_free_rate
    strategy_excess_return = strategy_annualized - risk_free_rate
    
    spy_sharpe = spy_excess_return / spy_vol if spy_vol > 0 else 0
    strategy_sharpe = strategy_excess_return / strategy_vol if strategy_vol > 0 else 0
    
    # Calculate Sortino ratio (penalizes downside volatility only)
    spy_downside_returns = df_clean[df_clean['SPY_Returns'] < 0]['SPY_Returns']
    strategy_downside_returns = df_clean[df_clean['Strategy_Return'] < 0]['Strategy_Return']
    
    spy_downside_vol = spy_downside_returns.std() * np.sqrt(12) if len(spy_downside_returns) > 0 else 0
    strategy_downside_vol = strategy_downside_returns.std() * np.sqrt(12) if len(strategy_downside_returns) > 0 else 0
    
    spy_sortino = spy_excess_return / spy_downside_vol if spy_downside_vol > 0 else 0
    strategy_sortino = strategy_excess_return / strategy_downside_vol if strategy_downside_vol > 0 else 0
    
    # Maximum drawdown
    spy_max_dd = df_clean['SPY_Drawdown'].min()
    strategy_max_dd = df_clean['Strategy_Drawdown'].min()
    
    # Win rate (positive return months)
    spy_win_rate = (df_clean['SPY_Returns'] > 0).sum() / len(df_clean) * 100
    strategy_win_rate = (df_clean['Strategy_Return'] > 0).sum() / len(df_clean) * 100
    
    # Calculate by regime
    regime_stats = df_clean.groupby('Regime').agg({
        'Strategy_Return': ['count', 'mean', 'std'],
        'SPY_Returns': 'mean'
    }).round(4)
    
    metrics = {
        'spy': {
            'total_return': float(spy_total_return),
            'annualized_return': float(spy_annualized),
            'excess_return': float(spy_excess_return),
            'volatility': float(spy_vol),
            'sharpe_ratio': float(spy_sharpe),
            'sortino_ratio': float(spy_sortino),
            'max_drawdown': float(spy_max_dd),
            'win_rate': float(spy_win_rate),
            'n_months': len(df_clean)
        },
        'strategy': {
            'total_return': float(strategy_total_return),
            'annualized_return': float(strategy_annualized),
            'excess_return': float(strategy_excess_return),
            'volatility': float(strategy_vol),
            'sharpe_ratio': float(strategy_sharpe),
            'sortino_ratio': float(strategy_sortino),
            'max_drawdown': float(strategy_max_dd),
            'win_rate': float(strategy_win_rate),
            'n_months': len(df_clean)
        },
        'outperformance': {
            'total_return': float(strategy_total_return - spy_total_return),
            'annualized_return': float(strategy_annualized - spy_annualized),
            'sharpe_improvement': float(strategy_sharpe - spy_sharpe),
            'sortino_improvement': float(strategy_sortino - spy_sortino),
            'max_dd_improvement': float(strategy_max_dd - spy_max_dd)
        },
        'risk_free_rate': float(risk_free_rate),
        'regime_stats': {str(k): {str(k2): float(v2) for k2, v2 in v.items()} for k, v in regime_stats.to_dict('index').items()} if len(regime_stats) > 0 else {}
    }
    
    return metrics


def run_backtest():
    """Run strategy backtest"""
    print("="*60)
    print("HY-IG Spread Strategy Backtesting")
    print("="*60)
    
    df = load_data()
    print(f"\nLoaded {len(df)} monthly records")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    
    # Identify Fed rate changes
    print("\nIdentifying Fed Funds Rate changes...")
    if 'FEDFUNDS' in df.columns:
        df, rate_periods = identify_fed_rate_changes(df)
        print(f"  Found {len(rate_periods)} rate change periods")
    else:
        rate_periods = []
        print("  WARNING: Fed Funds Rate data not available")
    
    # Run backtest
    print("\nRunning backtest...")
    df_backtest = backtest_strategy(df)
    
    # Calculate metrics
    print("Calculating performance metrics...")
    metrics = calculate_performance_metrics(df_backtest, risk_free_rate=RISK_FREE_RATE)
    
    if metrics is None:
        print("ERROR: Could not calculate metrics - insufficient data")
        return None, None
    
    # Calculate performance by Fed rate periods
    print("Calculating performance by Fed rate change periods...")
    fed_period_metrics = calculate_performance_by_fed_periods(df_backtest)
    metrics['fed_rate_periods'] = fed_period_metrics
    
    # Generate current strategy review (past 1 year)
    print("Generating current strategy review...")
    current_review = generate_current_strategy_review(df_backtest, lookback_months=12)
    print(f"  Generated {len(current_review)} review records")
    
    # Print results
    print(f"\n{'='*60}")
    print("BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"\nSPY Performance:")
    print(f"  Total Return: {metrics['spy']['total_return']:.2f}%")
    print(f"  Annualized Return: {metrics['spy']['annualized_return']:.2f}%")
    print(f"  Sharpe Ratio: {metrics['spy']['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics['spy']['max_drawdown']:.2f}%")
    print(f"  Win Rate: {metrics['spy']['win_rate']:.1f}%")
    
    print(f"\nStrategy Performance:")
    print(f"  Total Return: {metrics['strategy']['total_return']:.2f}%")
    print(f"  Annualized Return: {metrics['strategy']['annualized_return']:.2f}%")
    print(f"  Sharpe Ratio: {metrics['strategy']['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics['strategy']['max_drawdown']:.2f}%")
    print(f"  Win Rate: {metrics['strategy']['win_rate']:.1f}%")
    
    print(f"\nOutperformance:")
    print(f"  Total Return: {metrics['outperformance']['total_return']:.2f}%")
    print(f"  Annualized Return: {metrics['outperformance']['annualized_return']:.2f}%")
    print(f"  Sharpe Improvement: {metrics['outperformance']['sharpe_improvement']:.2f}")
    
    # Save results
    df_backtest.to_csv(OUTPUT_DIR / "strategy_backtest.csv")
    
    # Prepare JSON for web interface
    backtest_json = {
        'metadata': {
            'backtest_date': datetime.now().isoformat(),
            'date_range': {
                'start': str(df_backtest.index.min()),
                'end': str(df_backtest.index.max())
            }
        },
        'performance_metrics': metrics,
        'fed_rate_periods': rate_periods,
        'current_strategy_review': current_review,
        'monthly_data': {
            'dates': df_backtest.index.strftime("%Y-%m-%d").tolist(),
            'spy_returns': df_backtest['SPY_Returns'].fillna("null").tolist(),
            'strategy_returns': df_backtest['Strategy_Return'].fillna("null").tolist(),
            'spy_cumulative': df_backtest['SPY_Cumulative'].fillna("null").tolist(),
            'strategy_cumulative': df_backtest['Strategy_Cumulative'].fillna("null").tolist(),
            'spy_drawdown': df_backtest['SPY_Drawdown'].fillna("null").tolist(),
            'strategy_drawdown': df_backtest['Strategy_Drawdown'].fillna("null").tolist(),
            'regime': df_backtest['Regime'].fillna("null").tolist(),
            'position_size': df_backtest['Position_Size'].fillna("null").tolist(),
            'spread': df_backtest['HY_IG_Spread'].fillna("null").tolist(),
            'fedfunds': df_backtest['FEDFUNDS'].fillna("null").tolist() if 'FEDFUNDS' in df_backtest.columns else ["null"] * len(df_backtest),
            'fed_rate_change_type': df_backtest['Fed_Rate_Change_Type'].fillna("none").tolist() if 'Fed_Rate_Change_Type' in df_backtest.columns else ["none"] * len(df_backtest)
        }
    }
    
    with open(OUTPUT_DIR / "strategy_backtest.json", "w") as f:
        json.dump(backtest_json, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"Results saved to {OUTPUT_DIR}")
    print(f"{'='*60}")
    
    return df_backtest, metrics


if __name__ == "__main__":
    run_backtest()
