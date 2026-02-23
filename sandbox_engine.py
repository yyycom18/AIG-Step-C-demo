"""
Strategy Sandbox Engine (Layer 2) — E1 Transformation, E2 Threshold, E3 Position, Backtest, Metrics.
Uses only Tier1 indicator series and Tier1 ETF return series; no data fetch.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any

# Default rolling window for Z-score (configurable in UI, fixed default)
DEFAULT_Z_WINDOW = 60


# ---------- E1: Transformation Module ----------
def transform_signal(
    series: pd.Series,
    method: str,
    z_window: int = DEFAULT_Z_WINDOW,
) -> Tuple[pd.Series, pd.DatetimeIndex]:
    """
    E1: Return (signal_series, valid_date_index).
    Methods: Raw Level, Z-score, Percentile Rank, Momentum (1M/3M/6M), Rate of Change.
    """
    s = series.dropna().sort_index()
    if s.empty:
        return pd.Series(dtype=float), pd.DatetimeIndex([])

    if method == "Raw Level":
        out = s.copy()
    elif method == "Z-score":
        roll = s.rolling(window=min(z_window, len(s)), min_periods=max(1, min(z_window, len(s)) // 2))
        mu = roll.mean()
        std = roll.std()
        out = (s - mu) / std.replace(0, np.nan)
    elif method == "Percentile Rank":
        # Rolling percentile rank 0-100
        out = s.rolling(window=min(z_window, len(s)), min_periods=1).apply(
            lambda x: (pd.Series(x).rank(pct=True).iloc[-1] * 100) if len(x) else np.nan,
            raw=False,
        )
    elif method == "Momentum 1M":
        out = s - s.shift(1)
    elif method == "Momentum 3M":
        out = s - s.shift(3)
    elif method == "Momentum 6M":
        out = s - s.shift(6)
    elif method == "Rate of Change":
        out = s.pct_change(1)
    else:
        out = s.copy()

    out = out.dropna()
    return out, out.index


# ---------- E2: Threshold Module ----------
def apply_threshold(
    signal: pd.Series,
    rule: str,
    above_pct: float = 70.0,
    below_pct: float = 30.0,
) -> pd.Series:
    """
    E2: Binary signal (1 = active, 0 = inactive).
    Rules: Above X percentile, Below X percentile, Cross Median, Z-score > +1 / < -1, Momentum > 0.
    """
    if signal.empty:
        return pd.Series(dtype=float)

    if rule == "Above X percentile":
        thresh = signal.quantile(above_pct / 100.0)
        binary = (signal >= thresh).astype(int)
    elif rule == "Below X percentile":
        thresh = signal.quantile(below_pct / 100.0)
        binary = (signal <= thresh).astype(int)
    elif rule == "Cross Median":
        med = signal.median()
        binary = (signal > med).astype(int)
    elif rule == "Z-score > +1":
        binary = (signal > 1).astype(int)
    elif rule == "Z-score < -1":
        binary = (signal < -1).astype(int)
    elif rule == "Momentum > 0":
        binary = (signal > 0).astype(int)
    else:
        binary = (signal > signal.median()).astype(int)

    return binary.reindex(signal.index).fillna(0).astype(int)


# ---------- E3: Position Logic Module ----------
def position_logic(binary: pd.Series, mode: str) -> pd.Series:
    """
    E3: Exposure series in [0, 1].
    Modes: Long Only (In/Out), Risk Reduction (50%), Full Defensive (0%).
    """
    if binary.empty:
        return pd.Series(dtype=float)
    if mode == "Long Only (In/Out)":
        return binary.astype(float)
    if mode == "Risk Reduction (50% exposure)":
        return (binary * 0.5).astype(float)
    if mode == "Full Defensive (0% exposure)":
        return pd.Series(0.0, index=binary.index)
    return binary.astype(float)


# ---------- Backtest Engine ----------
def run_backtest(
    exposure: pd.Series,
    etf_return: pd.Series,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Simple monthly return compounding: strategy_return = exposure * etf_return.
    No leverage, no transaction cost. Returns (strategy_returns, strategy_cumulative, exposure_aligned).
    """
    # Align to common index
    idx = exposure.index.union(etf_return.index).drop_duplicates().sort_values()
    ex = exposure.reindex(idx).ffill().bfill().fillna(0).clip(0, 1)
    ret = etf_return.reindex(idx).fillna(0)
    strat_ret = ex * ret
    strat_cum = (1 + strat_ret / 100).cumprod()
    return strat_ret, strat_cum, ex


# ---------- Mandatory Evaluation Metrics (Guardrail 1) ----------
def evaluation_metrics(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 4.0,
) -> Dict[str, float]:
    """Total Return, CAGR, Sharpe, Max Drawdown, Volatility, Win Rate, Calmar."""
    s = strategy_returns.dropna()
    b = benchmark_returns.reindex(s.index).fillna(0)
    if s.empty or len(s) < 2:
        return _empty_metrics()

    n_years = (s.index[-1] - s.index[0]).days / 365.25
    if n_years <= 0:
        n_years = len(s) / 12.0

    # Strategy
    cum_s = (1 + s / 100).cumprod()
    total_ret_s = (cum_s.iloc[-1] / cum_s.iloc[0] - 1) * 100
    cagr_s = ((cum_s.iloc[-1] / cum_s.iloc[0]) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
    vol_s = s.std() * np.sqrt(12)
    sharpe_s = (cagr_s - risk_free_rate) / vol_s if vol_s > 0 else 0
    dd_s = (cum_s / cum_s.cummax() - 1) * 100
    max_dd_s = dd_s.min()
    win_rate_s = (s > 0).sum() / len(s) * 100
    calmar_s = cagr_s / abs(max_dd_s) if max_dd_s != 0 else 0

    # Benchmark (ETF buy & hold)
    cum_b = (1 + b / 100).cumprod()
    total_ret_b = (cum_b.iloc[-1] / cum_b.iloc[0] - 1) * 100
    cagr_b = ((cum_b.iloc[-1] / cum_b.iloc[0]) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
    vol_b = b.std() * np.sqrt(12)
    sharpe_b = (cagr_b - risk_free_rate) / vol_b if vol_b > 0 else 0
    dd_b = (cum_b / cum_b.cummax() - 1) * 100
    max_dd_b = dd_b.min()
    win_rate_b = (b > 0).sum() / len(b) * 100
    calmar_b = cagr_b / abs(max_dd_b) if max_dd_b != 0 else 0

    return {
        "strategy": {
            "total_return": total_ret_s,
            "cagr": cagr_s,
            "sharpe_ratio": sharpe_s,
            "max_drawdown": max_dd_s,
            "volatility": vol_s,
            "win_rate": win_rate_s,
            "calmar_ratio": calmar_s,
        },
        "benchmark": {
            "total_return": total_ret_b,
            "cagr": cagr_b,
            "sharpe_ratio": sharpe_b,
            "max_drawdown": max_dd_b,
            "volatility": vol_b,
            "win_rate": win_rate_b,
            "calmar_ratio": calmar_b,
        },
    }


def _empty_metrics() -> Dict[str, Any]:
    e = {
        "total_return": 0.0,
        "cagr": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "volatility": 0.0,
        "win_rate": 0.0,
        "calmar_ratio": 0.0,
    }
    return {"strategy": e.copy(), "benchmark": e.copy()}


# ---------- Sample Size Metrics (Guardrail 3) ----------
def sample_size_metrics(exposure: pd.Series) -> Tuple[Dict[str, Any], bool]:
    """
    N trades, N active periods, avg/max/min holding, % time in market.
    Returns (metrics_dict, warning_flag). Warning if N_trades < 5 or active_periods < 5% of dataset.
    """
    if exposure.empty:
        return {
            "n_trades": 0,
            "n_active_periods": 0,
            "avg_holding_period": 0.0,
            "max_holding_period": 0,
            "min_holding_period": 0,
            "pct_time_in_market": 0.0,
        }, True

    active = (exposure > 0).astype(int)
    n_active = int(active.sum())
    n_total = len(active)
    pct_active = (n_active / n_total * 100) if n_total > 0 else 0

    # Trades: number of transitions 0->1 (entries)
    entries = (active.diff() == 1).sum()
    n_trades = int(entries) if not pd.isna(entries) else 0

    # Holding periods: consecutive 1s
    holding_periods = []
    count = 0
    for v in active:
        if v > 0:
            count += 1
        else:
            if count > 0:
                holding_periods.append(count)
            count = 0
    if count > 0:
        holding_periods.append(count)
    avg_hold = np.mean(holding_periods) if holding_periods else 0.0
    max_hold = max(holding_periods) if holding_periods else 0
    min_hold = min(holding_periods) if holding_periods else 0

    warning = (n_trades < 5) or (pct_active < 5.0)
    return {
        "n_trades": n_trades,
        "n_active_periods": n_active,
        "avg_holding_period": float(avg_hold),
        "max_holding_period": int(max_hold),
        "min_holding_period": int(min_hold),
        "pct_time_in_market": float(pct_active),
    }, warning


# ---------- Full Sandbox Run ----------
def run_sandbox(
    indicator_series: pd.Series,
    etf_return_series: pd.Series,
    transformation: str,
    threshold_rule: str,
    position_mode: str,
    above_pct: float = 70.0,
    below_pct: float = 30.0,
    z_window: int = DEFAULT_Z_WINDOW,
    date_min: Optional[pd.Timestamp] = None,
    date_max: Optional[pd.Timestamp] = None,
) -> Dict[str, Any]:
    """
    Single entry: build signal -> binary -> exposure -> backtest -> metrics.
    Benchmark = ETF buy & hold (exposure 1). All on common date range.
    """
    # Restrict date range
    idx = indicator_series.index.intersection(etf_return_series.index).sort_values()
    if date_min is not None:
        idx = idx[idx >= date_min]
    if date_max is not None:
        idx = idx[idx <= date_max]
    if len(idx) < 12:
        return {"error": "Insufficient data after date filter (need ≥12 months)."}

    ind = indicator_series.reindex(idx).ffill().bfill().dropna()
    ret = etf_return_series.reindex(idx).fillna(0)
    if ind.empty:
        return {"error": "No valid indicator in range."}

    # E1
    signal, _ = transform_signal(ind, transformation, z_window=z_window)
    if signal.empty:
        return {"error": "Transformation produced no valid signal."}
    # Re-align return to signal
    ret = ret.reindex(signal.index).fillna(0)

    # E2
    binary = apply_threshold(signal, threshold_rule, above_pct=above_pct, below_pct=below_pct)
    binary = binary.reindex(signal.index).fillna(0).astype(int)

    # E3
    exposure = position_logic(binary, position_mode)

    # Backtest: strategy
    strat_ret, strat_cum, exposure_aligned = run_backtest(exposure, ret)
    # Benchmark: buy & hold (exposure 1)
    bench_ret = ret.reindex(strat_ret.index).fillna(0)
    bench_cum = (1 + bench_ret / 100).cumprod()
    bench_dd = (bench_cum / bench_cum.cummax() - 1) * 100
    strat_dd = (strat_cum / strat_cum.cummax() - 1) * 100

    metrics = evaluation_metrics(strat_ret, bench_ret)
    sample_metrics, sample_warning = sample_size_metrics(exposure_aligned)

    return {
        "strategy_returns": strat_ret,
        "strategy_cumulative": strat_cum,
        "strategy_drawdown": strat_dd,
        "benchmark_returns": bench_ret,
        "benchmark_cumulative": bench_cum,
        "benchmark_drawdown": bench_dd,
        "exposure": exposure_aligned,
        "dates": strat_cum.index,
        "evaluation_metrics": metrics,
        "sample_size_metrics": sample_metrics,
        "sample_size_warning": sample_warning,
        "config": {
            "transformation": transformation,
            "threshold_rule": threshold_rule,
            "position_mode": position_mode,
            "above_pct": above_pct,
            "below_pct": below_pct,
            "z_window": z_window,
            "date_min": str(date_min) if date_min is not None else None,
            "date_max": str(date_max) if date_max is not None else None,
        },
    }
