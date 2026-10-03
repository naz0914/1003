from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from backend.app.schemas.temperature import (
    LatestTemperatureResponse, GeoJSONResponse, StationTemperature
)
from backend.app.services.temperature_service import temperature_service

router = APIRouter(prefix="/api/temperature", tags=["Temperature"])


@router.get("/latest", response_model=LatestTemperatureResponse)
async def get_latest_temperature(
    county: Optional[str] = Query(None, description="依縣市過濾，如 '臺北市'"),
    min_temp: Optional[float] = Query(None, description="最低氣溫過濾門檻"),
    max_temp: Optional[float] = Query(None, description="最高氣溫過濾門檻"),
    max_altitude: Optional[float] = Query(None, description="最高海拔過濾 (如 1000 排除高山測站)"),
    min_altitude: Optional[float] = Query(None, description="最低海拔過濾")
):
    """
    9.1 取得所有有效的最新測站觀測資料
    支援縣市、氣溫區間與海拔高度篩選
    """
    try:
        data = temperature_service.get_latest()
        stations = data.stations

        if county and county != "全部":
            stations = [s for s in stations if s.county == county]
        if min_temp is not None:
            stations = [s for s in stations if s.temperature_c >= min_temp]
        if max_temp is not None:
            stations = [s for s in stations if s.temperature_c <= max_temp]
        if max_altitude is not None:
            stations = [s for s in stations if (s.altitude_m is None or s.altitude_m <= max_altitude)]
        if min_altitude is not None:
            stations = [s for s in stations if (s.altitude_m is not None and s.altitude_m >= min_altitude)]

        return LatestTemperatureResponse(
            source=data.source,
            updated_at=data.updated_at,
            count=len(stations),
            stations=stations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取 CWA 氣溫資料失敗: {str(e)}")


@router.get("/geojson", response_model=GeoJSONResponse)
async def get_temperature_geojson():
    """
    9.2 取得適用於 Leaflet GeoJSON 的圖層格式
    """
    try:
        return temperature_service.get_geojson()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"產生 GeoJSON 失敗: {str(e)}")


@router.get("/top-hottest", response_model=List[StationTemperature])
async def get_top_hottest_stations(limit: int = Query(10, ge=1, le=50)):
    """
    Section 28 延伸功能: 取得全台前 N 大最熱測站排行
    """
    return temperature_service.get_top_hottest(limit=limit)


@router.get("/stations/{station_id}", response_model=StationTemperature)
async def get_station_detail(station_id: str):
    """
    9.3 取得單一測站的詳細觀測數據
    """
    st = temperature_service.get_station_by_id(station_id)
    if not st:
        raise HTTPException(status_code=404, detail=f"找不到測站編號: {station_id}")
    return st


@router.post("/refresh", response_model=LatestTemperatureResponse)
async def refresh_cwa_data():
    """
    強制清除快取並從 CWA API 重新抓取即時數據
    """
    try:
        return temperature_service.get_latest(force_refresh=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新整理 CWA 資料失敗: {str(e)}")
