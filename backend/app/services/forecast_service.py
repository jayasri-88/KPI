"""
Forecasting Service
Orchestrates sales demand forecasting, model loading/training, and schema serialization.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.schemas import ForecastDataPoint, ModelEvaluationMetrics, SalesForecastResponse
from ml.data_loader import load_daily_sales
from ml.forecaster import get_forecast


def generate_sales_forecast(
    db: Session,
    days: int = 30,
    store_id: Optional[str] = None,
    force_retrain: bool = False,
) -> SalesForecastResponse:
    """
    Generates or retrieves cached retail sales forecast for 7 or 30 days.
    """
    # 1. Load actual sales history from PostgreSQL
    df = load_daily_sales(db, store_id=store_id)
    if df.empty or len(df) < 14:
        raise ValueError("Insufficient historical sales data to generate forecast (minimum 14 days required).")

    # 2. Get forecast (from disk/cache or trained on demand)
    raw = get_forecast(df, horizon_days=days, store_id=store_id, force_retrain=force_retrain)

    # 3. Combine historical tail (last 45 days) + forecast into single timeline
    data_points = []

    # Historical points
    for h in raw["historical_data"]:
        data_points.append(
            ForecastDataPoint(
                date=h["date"],
                actual_sales=h["actual_sales"],
                forecast_sales=None,
                lower_bound=None,
                upper_bound=None,
                is_forecast=False,
            )
        )

    # Forecast points
    for f in raw["forecast_data"]:
        data_points.append(
            ForecastDataPoint(
                date=f["date"],
                actual_sales=None,
                forecast_sales=f["forecast_sales"],
                lower_bound=f["lower_bound"],
                upper_bound=f["upper_bound"],
                is_forecast=True,
            )
        )

    # Anchor point: connect the last historical day with the forecast start
    if raw["historical_data"] and raw["forecast_data"]:
        last_hist = data_points[len(raw["historical_data"]) - 1]
        last_hist.forecast_sales = last_hist.actual_sales
        last_hist.lower_bound = last_hist.actual_sales
        last_hist.upper_bound = last_hist.actual_sales

    metrics = ModelEvaluationMetrics(
        mae=raw["evaluation_metrics"].get("mae", 0.0),
        rmse=raw["evaluation_metrics"].get("rmse", 0.0),
        mape=raw["evaluation_metrics"].get("mape", 0.0),
        wape=raw["evaluation_metrics"].get("wape", 0.0),
        r2=raw["evaluation_metrics"].get("r2", 0.0),
    )

    return SalesForecastResponse(
        model_name=raw["model_name"],
        horizon_days=raw["horizon_days"],
        store_id=raw["store_id"],
        trained_at=raw["trained_at"],
        last_observed_date=raw["last_observed_date"],
        evaluation_metrics=metrics,
        features_used=raw["features_used"],
        total_forecast_revenue=raw["total_forecast_revenue"],
        avg_daily_forecast=raw["avg_daily_forecast"],
        data=data_points,
    )
