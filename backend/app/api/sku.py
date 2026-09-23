from fastapi import APIRouter

from app.services.sku_service import (
    get_sku_intelligence,
    get_sku_region_comparison,
)


router = APIRouter(
    tags=["SKU Intelligence"],
)


@router.get("/intelligence")
def sku_intelligence():
    return get_sku_intelligence()


@router.get("/{product_id}/regions")
def sku_region_comparison(product_id: int):
    return {
        "product_id": product_id,
        "data": get_sku_region_comparison(
            product_id
        ),
    }