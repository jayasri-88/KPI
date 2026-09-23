from fastapi import APIRouter

from app.services.analytics_service import (
    get_category_performance,
    get_region_performance,
    get_sales_trend,
    get_sku_performance,
)


router = APIRouter(
    tags=["Analytics"],
)


@router.get("/sales-trend")
def sales_trend():
    return {
        "data": get_sales_trend()
    }


@router.get("/sku-performance")
def sku_performance():
    return {
        "data": get_sku_performance()
    }


@router.get("/region-performance")
def region_performance():
    return {
        "data": get_region_performance()
    }


@router.get("/category-performance")
def category_performance():
    return {
        "data": get_category_performance()
    }