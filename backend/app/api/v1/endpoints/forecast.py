"""
Forecasting API Endpoints
Generates 7-day and 30-day retail demand forecasts using Prophet and Scikit-learn.
"""

import uuid
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_active_admin
from app.database import get_db
from app.models import User
from app.schemas import SalesForecastResponse
from app.core.cache import TTL_FORECAST, cache_manager
from app.services import forecast_service
from ml.feature_engineering import explain_features

router = APIRouter()


@router.get(
    "/sales",
    response_model=SalesForecastResponse,
    summary="Get 7-day or 30-day sales forecast",
    description="Returns future daily retail sales projections, confidence intervals (yhat_lower, yhat_upper), historical tail, and out-of-time evaluation metrics with Redis caching.",
)
def get_sales_forecast(
    days: Optional[int] = Query(None, ge=7, le=90, description="Forecast horizon in days (e.g. 7 or 30)"),
    horizon_days: Optional[int] = Query(None, ge=7, le=90, description="Alias for days parameter"),
    store_id: Optional[uuid.UUID] = Query(None, description="Optional store filter for store-specific demand forecast"),
    force_retrain: bool = Query(False, description="Force fresh model retraining and disk artifact update"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    selected_days = horizon_days if horizon_days is not None else (days if days is not None else 30)

    cache_key = cache_manager.build_key(
        "forecast:sales",
        days=selected_days,
        store_id=str(store_id) if store_id else None,
    )

    if not force_retrain:
        cached_data = cache_manager.get(cache_key)
        if cached_data is not None:
            return cached_data

    try:
        data = forecast_service.generate_sales_forecast(
            db=db,
            days=selected_days,
            store_id=str(store_id) if store_id else None,
            force_retrain=force_retrain,
        )
        cache_manager.set(cache_key, data, ttl=TTL_FORECAST)
        return data
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting pipeline error: {str(e)}",
        )


@router.post(
    "/train",
    summary="Retrain and persist forecasting model",
    description="Manually triggers training on latest PostgreSQL sales data and saves updated model artifact to disk. Invalidates forecast cache.",
)
def retrain_forecast_model(
    store_id: Optional[uuid.UUID] = Query(None, description="Optional store ID to retrain"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    try:
        fc = forecast_service.generate_sales_forecast(
            db=db,
            days=30,
            store_id=str(store_id) if store_id else None,
            force_retrain=True,
        )
        cache_manager.delete_pattern("forecast:*")
        return {
            "status": "success",
            "message": "Model retrained and persisted successfully.",
            "model_name": fc.model_name,
            "trained_at": fc.trained_at,
            "evaluation_metrics": fc.evaluation_metrics,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model retraining failed: {str(e)}",
        )



@router.get(
    "/features",
    response_model=Dict[str, str],
    summary="Explain forecasting features",
    description="Returns detailed descriptions of time-series, cyclical, lag, and rolling features used in the ML model.",
)
def get_features_explanation(
    current_user: User = Depends(get_current_user),
):
    return explain_features()
