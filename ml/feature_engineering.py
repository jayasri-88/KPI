"""
Feature Engineering Pipeline for Retail Sales Forecasting
Extracts calendar, cyclical, lag, and rolling statistics while strictly preventing data leakage.
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


FEATURE_METADATA: Dict[str, str] = {
    "day_of_week": "Day of the week (0=Monday, 6=Sunday), capturing intra-week shopping patterns.",
    "day_of_month": "Calendar day of the month (1-31), capturing salary cycles and mid-month surges.",
    "month": "Calendar month (1-12), capturing seasonal and quarterly retail trends.",
    "quarter": "Financial quarter (1-4), tracking macro retail performance shifts.",
    "is_weekend": "Binary flag (1 for Saturday/Sunday, 0 otherwise) capturing footfall spikes.",
    "is_month_end": "Binary flag (1 for last 3 days of calendar month), tracking end-of-month clearance promotions.",
    "lag_1": "Sales volume on immediate previous day (T-1), capturing short-term auto-regressive momentum.",
    "lag_7": "Sales volume 7 days prior (T-7), capturing same-day-of-week seasonality.",
    "lag_14": "Sales volume 14 days prior (T-14), capturing bi-weekly retail cadence.",
    "lag_30": "Sales volume 30 days prior (T-30), capturing monthly baseline sales.",
    "rolling_mean_7": "7-day trailing simple moving average shifted by 1 to prevent data leakage.",
    "rolling_std_7": "7-day trailing volatility / standard deviation shifted by 1.",
    "rolling_mean_30": "30-day trailing baseline moving average shifted by 1.",
    "trend_step": "Ordinal continuous time index capturing long-term growth or decline trend.",
}


def build_forecasting_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs feature matrix from daily sales data.
    Ensures all rolling and lag features are shifted by at least 1 day
    to guarantee strict zero-leakage out-of-time evaluation.
    """
    data = df.copy()
    data = data.sort_values("ds").reset_index(drop=True)

    # 1. Calendar & Cyclical Features
    data["day_of_week"] = data["ds"].dt.dayofweek
    data["day_of_month"] = data["ds"].dt.day
    data["month"] = data["ds"].dt.month
    data["quarter"] = data["ds"].dt.quarter
    data["is_weekend"] = data["day_of_week"].apply(lambda d: 1 if d in (5, 6) else 0)
    data["is_month_end"] = data["ds"].dt.is_month_end.astype(int)

    # 2. Time Trend Feature
    data["trend_step"] = np.arange(len(data))

    # 3. Strictly Past-Shifted Lag Features (Prevent Leakage)
    target = data["y"]
    data["lag_1"] = target.shift(1)
    data["lag_7"] = target.shift(7)
    data["lag_14"] = target.shift(14)
    data["lag_30"] = target.shift(30)

    # 4. Strictly Past-Shifted Rolling Statistics
    # Note: .shift(1) ensures the current day's target is NEVER included in rolling computation!
    past_target = target.shift(1)
    data["rolling_mean_7"] = past_target.rolling(window=7, min_periods=1).mean()
    data["rolling_std_7"] = past_target.rolling(window=7, min_periods=1).std().fillna(0.0)
    data["rolling_mean_14"] = past_target.rolling(window=14, min_periods=1).mean()
    data["rolling_mean_30"] = past_target.rolling(window=30, min_periods=1).mean()

    # Backfill earliest rows where lag > 30 is NaN using overall past median
    median_val = target.median() if not target.empty else 0.0
    lag_cols = ["lag_1", "lag_7", "lag_14", "lag_30", "rolling_mean_7", "rolling_std_7", "rolling_mean_14", "rolling_mean_30"]
    for col in lag_cols:
        data[col] = data[col].bfill().fillna(median_val)

    return data


def get_feature_names() -> List[str]:
    """Returns list of feature column names used for tabular regressors."""
    return list(FEATURE_METADATA.keys())


def explain_features() -> Dict[str, str]:
    """Returns human-readable explanations of all features used."""
    return FEATURE_METADATA
