from fastapi import APIRouter
from backend.app.schemas.temperature import HealthResponse
from backend.app.services.cache_service import cache_service

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    9.4 健康檢查端點
    回傳服務狀態、快取鮮度與 CWA 最新觀測時戳
    """
    cached_data, status = cache_service.get()
    latest_time = cache_service.get_latest_cwa_time()
    count = cached_data.count if cached_data else 0

    return HealthResponse(
        status="ok",
        cwa_cache_status=status,
        latest_cwa_time=latest_time,
        stations_count=count
    )
