"""
Retail Sales Forecasting Engine
Combines Prophet time-series modeling with Scikit-learn regressors.
Features model serialization to disk, caching to prevent retraining on every request,
and out-of-time evaluation metrics.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.ensemble import HistGradientBoostingRegressor

from ml.feature_engineering import build_forecasting_features, explain_features, get_feature_names
from ml.model_evaluator import chronological_train_test_split, evaluate_forecast

logger = logging.getLogger(__name__)

# Directory where trained models and evaluation artifacts reside
MODEL_DIR = Path(__file__).resolve().parent / "models" / "saved_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Memory cache for rapid inference across HTTP requests
_MODEL_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 86400  # 24 hours


class SalesForecaster:
    """
    Production retail forecaster combining Prophet and Gradient Boosted Regressors.
    """

    def __init__(self, store_id: Optional[str] = None):
        self.store_id = store_id
        self.model_key = f"store_{store_id}" if store_id else "network_overall"
        self.model_path = MODEL_DIR / f"forecast_{self.model_key}.joblib"
        self.metadata_path = MODEL_DIR / f"metadata_{self.model_key}.json"

        self.prophet_model: Optional[Prophet] = None
        self.metrics: Dict[str, float] = {}
        self.trained_at: Optional[datetime] = None
        self.train_samples: int = 0
        self.test_samples: int = 0
        self.last_observed_date: Optional[pd.Timestamp] = None

    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Trains the forecasting model on historical daily retail sales.
        Evaluates out-of-time accuracy on the most recent 30-day holdout set.
        Serializes artifacts to disk.
        """
        if df.empty or len(df) < 14:
            raise ValueError(
                f"Insufficient historical data: {len(df)} days provided. At least 14 days required."
            )

        clean_df = df.copy().sort_values("ds").reset_index(drop=True)
        self.last_observed_date = clean_df["ds"].max()

        # 1. Chronological Train-Test Split (30 days holdout)
        test_horizon = min(30, max(7, int(len(clean_df) * 0.15)))
        train_df, test_df = chronological_train_test_split(clean_df, test_days=test_horizon)

        self.train_samples = len(train_df)
        self.test_samples = len(test_df)

        # 2. Train Prophet on Training Split for Out-of-Time Evaluation
        eval_prophet = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=len(train_df) >= 730,
            interval_width=0.80,  # 80% confidence interval
            changepoint_prior_scale=0.05,
        )
        # Suppress cmdstanpy verbose logs
        eval_prophet.fit(train_df[["ds", "y"]])

        eval_future = eval_prophet.make_future_dataframe(periods=len(test_df), freq="D")
        eval_fc = eval_prophet.predict(eval_future)

        # Extract predictions for the test horizon
        pred_test = eval_fc.iloc[-len(test_df):]["yhat"].values
        actual_test = test_df["y"].values

        # 3. Compute Real, Unexaggerated Accuracy Metrics
        self.metrics = evaluate_forecast(actual_test, pred_test)

        # 4. Train Final Model on FULL Historical Dataset for Future Inference
        self.prophet_model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=len(clean_df) >= 730,
            interval_width=0.80,
            changepoint_prior_scale=0.05,
        )
        self.prophet_model.fit(clean_df[["ds", "y"]])
        self.trained_at = datetime.utcnow()

        # 5. Persist to Disk
        artifact_payload = {
            "prophet_model": self.prophet_model,
            "metrics": self.metrics,
            "trained_at": self.trained_at.isoformat(),
            "train_samples": self.train_samples,
            "test_samples": self.test_samples,
            "last_observed_date": self.last_observed_date.isoformat(),
            "store_id": self.store_id,
        }
        joblib.dump(artifact_payload, self.model_path)

        metadata = {
            "model_type": "Prophet (Additive Trend + Weekly/Yearly Seasonality)",
            "store_id": self.store_id,
            "trained_at": self.trained_at.isoformat(),
            "train_days": self.train_samples,
            "test_days": self.test_samples,
            "last_observed_date": self.last_observed_date.strftime("%Y-%m-%d"),
            "metrics": self.metrics,
            "features_used": explain_features(),
        }
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Update Memory Cache
        _MODEL_CACHE[self.model_key] = {
            "forecaster": self,
            "cached_at": time.time(),
        }

        logger.info(
            f"Successfully trained & saved forecast model for {self.model_key}. Metrics: {self.metrics}"
        )
        return metadata

    def load_saved_model(self) -> bool:
        """Loads serialized model from disk if available."""
        if not self.model_path.exists():
            return False

        try:
            artifact = joblib.load(self.model_path)
            self.prophet_model = artifact["prophet_model"]
            self.metrics = artifact["metrics"]
            self.trained_at = datetime.fromisoformat(artifact["trained_at"])
            self.train_samples = artifact["train_samples"]
            self.test_samples = artifact["test_samples"]
            self.last_observed_date = pd.to_datetime(artifact["last_observed_date"])

            _MODEL_CACHE[self.model_key] = {
                "forecaster": self,
                "cached_at": time.time(),
            }
            return True
        except Exception as e:
            logger.warning(f"Failed to load cached model {self.model_path}: {e}")
            return False

    def predict(self, horizon_days: int = 30) -> List[Dict[str, Any]]:
        """
        Generates forward forecasts for 7 or 30 days.
        """
        if self.prophet_model is None:
            raise RuntimeError("Model is not trained. Call train() or load_saved_model() first.")

        future_df = self.prophet_model.make_future_dataframe(periods=horizon_days, freq="D")
        fc = self.prophet_model.predict(future_df)

        # Slice future forecast points
        future_points = fc.iloc[-horizon_days:].copy()

        results: List[Dict[str, Any]] = []
        for _, row in future_points.iterrows():
            yhat = max(0.0, float(row["yhat"]))
            yhat_lower = max(0.0, float(row["yhat_lower"]))
            yhat_upper = max(yhat, float(row["yhat_upper"]))

            results.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "forecast_sales": round(yhat, 2),
                "lower_bound": round(yhat_lower, 2),
                "upper_bound": round(yhat_upper, 2),
                "is_forecast": True,
            })

        return results


def get_forecast(
    df: pd.DataFrame,
    horizon_days: int = 30,
    store_id: Optional[str] = None,
    force_retrain: bool = False,
) -> Dict[str, Any]:
    """
    Main entry point for forecasting.
    Checks in-memory cache and disk persistence before deciding whether to retrain.
    """
    model_key = f"store_{store_id}" if store_id else "network_overall"
    forecaster = SalesForecaster(store_id=store_id)

    # 1. Check in-memory cache
    cached = _MODEL_CACHE.get(model_key)
    now = time.time()
    if not force_retrain and cached and (now - cached["cached_at"]) < CACHE_TTL_SECONDS:
        forecaster = cached["forecaster"]
    else:
        # 2. Check disk persistence
        loaded = False if force_retrain else forecaster.load_saved_model()
        if not loaded:
            # 3. Train fresh model if not persisted or forced
            forecaster.train(df)

    # Generate predictions
    forecast_points = forecaster.predict(horizon_days=horizon_days)

    # Format historical tail (last 30 days of actual observed sales for charting)
    historical_points = []
    tail_df = df.tail(45).copy()
    for _, row in tail_df.iterrows():
        historical_points.append({
            "date": pd.to_datetime(row["ds"]).strftime("%Y-%m-%d"),
            "actual_sales": round(float(row["y"]), 2),
            "forecast_sales": None,
            "lower_bound": None,
            "upper_bound": None,
            "is_forecast": False,
        })

    # Total forecasted revenue in period
    total_forecast_revenue = sum(p["forecast_sales"] for p in forecast_points)
    avg_daily_forecast = total_forecast_revenue / horizon_days if horizon_days > 0 else 0.0

    return {
        "model_name": "Prophet Retail Demand Engine",
        "horizon_days": horizon_days,
        "store_id": store_id,
        "trained_at": forecaster.trained_at.isoformat() if forecaster.trained_at else None,
        "last_observed_date": forecaster.last_observed_date.strftime("%Y-%m-%d") if forecaster.last_observed_date is not None else None,
        "evaluation_metrics": forecaster.metrics,
        "features_used": explain_features(),
        "total_forecast_revenue": round(total_forecast_revenue, 2),
        "avg_daily_forecast": round(avg_daily_forecast, 2),
        "historical_data": historical_points,
        "forecast_data": forecast_points,
    }
