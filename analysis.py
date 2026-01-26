"""
Analysis script for HY-IG Spread vs SPY following the Time Series Relationship Framework
"""
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from statsmodels.tsa.stattools import grangercausalitytests
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import r2_score, mean_squared_error
import json
from datetime import datetime

# Configuration
DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_data():
    """Load prepared data"""
    df_monthly = pd.read_csv(DATA_DIR / "hyig_spy_monthly.csv", index_col=0, parse_dates=True)
    return df_monthly


def create_derivatives(df, col, prefix):
    """Create standard derivative series (Step 1)"""
    series = df[col]
    
    # Percentage changes
    df[f'{prefix}_MoM'] = series.pct_change(1) * 100
    df[f'{prefix}_QoQ'] = series.pct_change(3) * 100
    df[f'{prefix}_YoY'] = series.pct_change(12) * 100
    
    # Direction indicators
    df[f'{prefix}_MoM_Dir'] = np.sign(df[f'{prefix}_MoM'].fillna(0))
    df[f'{prefix}_YoY_Dir'] = np.sign(df[f'{prefix}_YoY'].fillna(0))
    
    # Z-score (60-month rolling)
    rolling_mean = series.rolling(60, min_periods=12).mean()
    rolling_std = series.rolling(60, min_periods=12).std()
    df[f'{prefix}_ZScore'] = (series - rolling_mean) / rolling_std
    
    return df


def correlation_analysis(df, x_cols, y_cols):
    """Step 2: Correlation Analysis with significance testing"""
    results = []
    for x_col in x_cols:
        for y_col in y_cols:
            valid = df[[x_col, y_col]].dropna()
            if len(valid) < 30:
                continue
            try:
                corr, pval = stats.pearsonr(valid[x_col], valid[y_col])
                results.append({
                    'X': x_col,
                    'Y': y_col,
                    'correlation': corr,
                    'p_value': pval,
                    'significant': pval < 0.05,
                    'n_obs': len(valid)
                })
            except (ValueError, TypeError) as e:
                print(f"    Skipping {x_col} vs {y_col}: {e}")
                continue
    return pd.DataFrame(results)


def lead_lag_analysis(df, x_col, y_col, max_lag=12):
    """
    Step 3: Lead-Lag Analysis using cross-correlation
    
    Interpretation:
    - lag < 0: X leads Y (X is earlier, predicts Y)
    - lag = 0: Contemporaneous correlation
    - lag > 0: Y leads X (Y is earlier, predicts X)
    """
    # Align data
    aligned = df[[x_col, y_col]].dropna()
    if len(aligned) < 50:
        print(f"    Insufficient data: {len(aligned)} observations (need ≥50)")
        return None, None
    
    x_series = aligned[x_col].values
    y_series = aligned[y_col].values
    
    # Validate data
    if np.std(x_series) == 0 or np.std(y_series) == 0:
        print(f"    Cannot calculate: One series has zero variance")
        return None, None
    
    # Normalize
    x_norm = (x_series - np.mean(x_series)) / np.std(x_series)
    y_norm = (y_series - np.mean(y_series)) / np.std(y_series)
    
    results = []
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # X leads Y: Compare X[0:lag] with Y[-lag:]
            # Example: lag=-1 means X[:-1] with Y[1:] (X is 1 month ahead)
            x_shifted = x_norm[:lag]        # X from start to lag
            y_aligned = y_norm[-lag:]       # Y from -lag onwards
        elif lag > 0:
            # Y leads X: Compare X[lag:] with Y[:-lag]
            # Example: lag=1 means X[1:] with Y[:-1] (Y is 1 month ahead)
            x_shifted = x_norm[lag:]        # X from lag onwards
            y_aligned = y_norm[:-lag]       # Y from start to -lag
        else:
            # Contemporaneous (lag=0)
            x_shifted = x_norm
            y_aligned = y_norm
        
        # Ensure minimum observations
        if len(x_shifted) < 30 or len(y_aligned) < 30:
            continue
        
        # Trim to same length (safety check, should be equal)
        min_len = min(len(x_shifted), len(y_aligned))
        x_shifted = x_shifted[:min_len]
        y_aligned = y_aligned[:min_len]
        
        try:
            corr, pval = stats.pearsonr(x_shifted, y_aligned)
            results.append({
                'lag': lag,
                'correlation': corr,
                'p_value': pval,
                'n_obs': min_len
            })
        except (ValueError, TypeError) as e:
            print(f"    Warning: Correlation failed at lag {lag}: {e}")
            continue
    
    if len(results) == 0:
        print(f"    No valid correlations calculated")
        return None, None
    
    results_df = pd.DataFrame(results)
    best_lag = results_df.loc[results_df['correlation'].abs().idxmax()]
    
    return results_df, best_lag


def granger_causality_test(df, x_col, y_col, max_lag=6):
    """Step 4: Granger Causality Testing"""
    aligned = df[[x_col, y_col]].dropna()
    if len(aligned) < 50:
        return None
    
    # Test X -> Y
    try:
        data = aligned[[x_col, y_col]].values
        result = grangercausalitytests(data, max_lag, verbose=False)
        
        # Extract p-values for each lag
        p_values = []
        for lag in range(1, max_lag + 1):
            try:
                p_val = result[lag][0]['ssr_ftest'][1]
                p_values.append({'lag': lag, 'p_value': p_val})
            except:
                continue
        
        return pd.DataFrame(p_values)
    except Exception as e:
        print(f"Granger causality test failed: {e}")
        return None


def safe_extract_correlation(df, x_col, y_col):
    """Safely extract correlation between two columns"""
    filtered = df[(df['X'] == x_col) & (df['Y'] == y_col)]
    if len(filtered) > 0:
        return float(filtered['correlation'].iloc[0])
    return None


def predictive_modeling(df, x_col, y_col, test_size=0.2):
    """Step 5: Predictive Modeling with ML"""
    aligned = df[[x_col, y_col]].dropna()
    if len(aligned) < 100:
        return None, None
    
    # Create lagged features
    features = []
    for lag in range(1, 13):  # 1 to 12 months
        aligned[f'{x_col}_lag{lag}'] = aligned[x_col].shift(lag)
        features.append(f'{x_col}_lag{lag}')
    
    model_df = aligned[[y_col] + features].dropna()
    if len(model_df) < 50:
        return None, None
    
    X = model_df[features].values
    y = model_df[y_col].values
    
    # Time series cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    scores = []
    
    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        score = r2_score(y_test, y_pred)
        scores.append(score)
    
    # Final model on all data
    final_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5)
    final_model.fit(X, y)
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': final_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    results = {
        'mean_r2': np.mean(scores),
        'std_r2': np.std(scores),
        'feature_importance': feature_importance.to_dict('records')
    }
    
    return results, final_model


def regime_analysis(df, spread_col, return_col, n_regimes=3):
    """Step 6: Regime Analysis"""
    aligned = df[[spread_col, return_col]].dropna()
    if len(aligned) < 50:
        return None
    
    # Define regimes based on spread percentiles
    if n_regimes == 3:
        thresholds = [
            aligned[spread_col].quantile(0.33),
            aligned[spread_col].quantile(0.67)
        ]
        aligned['regime'] = pd.cut(
            aligned[spread_col],
            bins=[-np.inf, thresholds[0], thresholds[1], np.inf],
            labels=['Low Spread', 'Medium Spread', 'High Spread']
        )
    else:
        # Use quartiles
        thresholds = [
            aligned[spread_col].quantile(0.25),
            aligned[spread_col].quantile(0.50),
            aligned[spread_col].quantile(0.75)
        ]
        aligned['regime'] = pd.cut(
            aligned[spread_col],
            bins=[-np.inf, thresholds[0], thresholds[1], thresholds[2], np.inf],
            labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4 (Highest)']
        )
    
    # Calculate performance by regime
    regime_stats = aligned.groupby('regime')[return_col].agg([
        'count', 'mean', 'std', 'sum'
    ]).round(4)
    regime_stats['sharpe'] = (regime_stats['mean'] / regime_stats['std']) * np.sqrt(12)  # Annualized
    
    # Add cumulative returns
    aligned['cumulative_return'] = aligned.groupby('regime')[return_col].cumsum()
    
    return {
        'regime_stats': regime_stats.to_dict('index'),
        'regime_data': aligned,
        'thresholds': thresholds if n_regimes == 4 else [thresholds[0], thresholds[1]]
    }


def run_full_analysis():
    """Run complete analysis following the framework"""
    print("="*60)
    print("HY-IG Spread vs SPY Analysis")
    print("="*60)
    print("\nStep 1: Data Preparation...")
    
    df = load_data()
    print(f"  Loaded {len(df)} monthly records")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")
    
    # Create derivatives
    df = create_derivatives(df, 'HY_IG_Spread', 'Spread')
    df = create_derivatives(df, 'SPY', 'SPY')
    print("  Created derivative series (MoM, QoQ, YoY, Z-Score)")
    
    # Step 2: Correlation Analysis
    print("\nStep 2: Correlation Analysis...")
    x_cols = ['HY_IG_Spread', 'Spread_MoM', 'Spread_QoQ', 'Spread_YoY', 'Spread_ZScore']
    y_cols = ['SPY_Returns', 'SPY_MoM', 'SPY_QoQ', 'SPY_YoY']
    corr_results = correlation_analysis(df, x_cols, y_cols)
    corr_results.to_csv(OUTPUT_DIR / "correlations.csv", index=False)
    print(f"  Calculated {len(corr_results)} correlation pairs")
    print(f"  Results saved to {OUTPUT_DIR / 'correlations.csv'}")
    
    # Step 3: Lead-Lag Analysis
    print("\nStep 3: Lead-Lag Analysis...")
    leadlag_results, best_lag = lead_lag_analysis(df, 'HY_IG_Spread', 'SPY_Returns', max_lag=12)
    if leadlag_results is not None:
        leadlag_results.to_csv(OUTPUT_DIR / "lead_lag.csv", index=False)
        print(f"  Best lag: {best_lag['lag']} months (correlation: {best_lag['correlation']:.3f})")
        print(f"  Results saved to {OUTPUT_DIR / 'lead_lag.csv'}")
    
    # Step 4: Granger Causality
    print("\nStep 4: Granger Causality Testing...")
    granger_results = granger_causality_test(df, 'HY_IG_Spread', 'SPY_Returns', max_lag=6)
    if granger_results is not None:
        print(f"  Granger causality test completed")
        print(f"  Minimum p-value: {granger_results['p_value'].min():.4f}")
    
    # Step 5: Predictive Modeling
    print("\nStep 5: Predictive Modeling...")
    model_results, model = predictive_modeling(df, 'HY_IG_Spread', 'SPY_Returns')
    if model_results is not None:
        print(f"  Mean R^2: {model_results['mean_r2']:.4f} (+/- {model_results['std_r2']:.4f})")
        print(f"  Top feature: {model_results['feature_importance'][0]['feature']}")
    
    # Step 6: Regime Analysis
    print("\nStep 6: Regime Analysis...")
    regime_results = regime_analysis(df, 'HY_IG_Spread', 'SPY_Returns', n_regimes=4)
    if regime_results is not None:
        print(f"  Regime statistics calculated")
        for regime, stats in regime_results['regime_stats'].items():
            print(f"    {regime}: Mean={stats['mean']:.2f}%, Sharpe={stats['sharpe']:.2f}")
    
    # Save summary results
    summary = {
        'analysis_date': datetime.now().isoformat(),
        'data_period': {
            'start': str(df.index.min()),
            'end': str(df.index.max()),
            'n_months': len(df),
            'total_records': len(df)
        },
        'correlation_summary': {
            'level_correlation': safe_extract_correlation(corr_results, 'HY_IG_Spread', 'SPY_Returns'),
            'n_significant': int(corr_results['significant'].sum()),
            'total_pairs_tested': len(corr_results)
        },
        'lead_lag': {
            'best_lag': int(best_lag['lag']) if best_lag is not None else None,
            'best_correlation': float(best_lag['correlation']) if best_lag is not None else None,
            'best_p_value': float(best_lag['p_value']) if best_lag is not None else None
        } if best_lag is not None else None,
        'predictive_modeling': {
            'mean_r2': float(model_results['mean_r2']) if model_results else None,
            'std_r2': float(model_results['std_r2']) if model_results else None,
            'top_features': [f['feature'] for f in model_results['feature_importance'][:3]] if model_results else None
        } if model_results else None,
        'regime_analysis': regime_results['regime_stats'] if regime_results else None
    }
    
    with open(OUTPUT_DIR / "analysis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print("Analysis Complete!")
    print(f"{'='*60}")
    print(f"Results saved to {OUTPUT_DIR}")
    
    return df, summary


if __name__ == "__main__":
    run_full_analysis()
