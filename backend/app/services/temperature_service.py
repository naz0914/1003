from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.app.schemas.temperature import (
    StationTemperature, LatestTemperatureResponse, 
    GeoJSONResponse, GeoJSONFeature, GeoJSONGeometry
)
from backend.app.services.cwa_client import CWAClient
from backend.app.services.cache_service import cache_service
from backend.app.config import settings

class TemperatureService:
    """氣溫服務邏輯層 (整合快取、CWA 客戶端與格式轉換)"""

    def __init__(self):
        self.cwa_client = CWAClient()

    def get_latest(self, force_refresh: bool = False) -> LatestTemperatureResponse:
        cached_data, status = cache_service.get()

        if not force_refresh and cached_data and status == "fresh":
            return cached_data

        # 重新獲取最新資料
        try:
            stations = self.cwa_client.fetch_observations()
            updated_at = datetime.now().isoformat()
            
            response = LatestTemperatureResponse(
                source="CWA",
                updated_at=updated_at,
                count=len(stations),
                stations=stations
            )
            # 存入快取
            latest_time = stations[0].observed_at if stations else updated_at
            cache_service.set(response, ttl_seconds=settings.CACHE_TTL_SECONDS, cwa_time=latest_time)
            return response
        except Exception as e:
            # 若獲取失敗但有過期快取，降級回傳過期快取 (Section 22)
            if cached_data:
                return cached_data
            raise e

    def get_geojson(self) -> GeoJSONResponse:
        latest = self.get_latest()
        features: List[GeoJSONFeature] = []

        for st in latest.stations:
            feature = GeoJSONFeature(
                geometry=GeoJSONGeometry(coordinates=[st.lon, st.lat]),
                properties={
                    "station_id": st.station_id,
                    "station_name": st.station_name,
                    "county": st.county,
                    "town": st.town,
                    "temperature_c": st.temperature_c,
                    "humidity_percent": st.humidity_percent,
                    "wind_speed_mps": st.wind_speed_mps,
                    "pressure_hpa": st.pressure_hpa,
                    "precipitation_mm": st.precipitation_mm,
                    "weather": st.weather,
                    "observed_at": st.observed_at
                }
            )
            features.append(feature)

        return GeoJSONResponse(features=features)

    def get_station_by_id(self, station_id: str) -> Optional[StationTemperature]:
        latest = self.get_latest()
        for st in latest.stations:
            if st.station_id == station_id:
                return st
        return None

    def get_top_hottest(self, limit: int = 10) -> List[StationTemperature]:
        latest = self.get_latest()
        sorted_stations = sorted(latest.stations, key=lambda s: s.temperature_c, reverse=True)
        return sorted_stations[:limit]

temperature_service = TemperatureService()
