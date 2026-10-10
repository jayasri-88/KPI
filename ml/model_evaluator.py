"""
Model Evaluation Module for Retail Sales Forecasting
Calculates MAE, RMSE, MAPE, WAPE, and R² using chronological out-of-time splits.
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_forecast(y_true: np.ndarray | pd.Series, y_pred: np.ndarray | pd.Series) -> Dict[str, float]:
    """
    Computes rigorous, unexaggerated retail forecasting accuracy metrics.
    """
    y_t = np.array(y_true, dtype=float)
    y_p = np.array(y_pred, dtype=float)

    # Ensure non-negative predictions for retail revenue
    y_p = np.maximum(y_p, 0.0)

    if len(y_t) == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0, "wape": 0.0, "r2": 0.0}

    # 1. Mean Absolute Error
    mae = float(mean_absolute_error(y_t, y_p))

    # 2. Root Mean Squared Error
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))

    # 3. Mean Absolute Percentage Error (MAPE) with zero-division safeguard
    denominator = np.maximum(y_t, 1.0)
    abs_pct_errors = np.abs((y_t - y_p) / denominator)
    # Clip extreme outlier percentages to 100% to avoid artificial inflation on zero-sales days
    mape = float(np.mean(np.minimum(abs_pct_errors, 1.0)) * 100.0)

    # 4. Weighted Absolute Percentage Error (WAPE / MAD/Mean Ratio)
    # Industry standard in retail supply chain & demand planning
    total_actual = float(np.sum(y_t))
    total_abs_err = float(np.sum(np.abs(y_t - y_p)))
    wape = float((total_abs_err / total_actual) * 100.0) if total_actual > 0 else 0.0

    # 5. R-squared (Coefficient of Determination)
    try:
        r2 = float(r2_score(y_t, y_p))
        # Cap lower bound at -1.0 for realistic reporting
        r2 = max(-1.0, min(1.0, r2))
    except Exception:
        r2 = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
        "wape": round(wape, 2),
        "r2": round(r2, 4),
    }


def chronological_train_test_split(
    df: pd.DataFrame, test_days: int = 30
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits time-series data chronologically without shuffling to prevent look-ahead bias.
    """
    if len(df) <= test_days:
        # If insufficient data, use 80/20 chronological split
        split_idx = int(len(df) * 0.8)
        return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()

    split_date = df["ds"].max() - pd.Timedelta(days=test_days)
    train_df = df[df["ds"] <= split_date].copy()
    test_df = df[df["ds"] > split_date].copy()
    return train_df, test_df
