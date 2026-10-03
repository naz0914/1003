from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class StationTemperature(BaseModel):
    station_id: str = Field(..., description="測站編號")
    station_name: str = Field(..., description="測站名稱")
    county: Optional[str] = Field(None, description="縣市名稱")
    town: Optional[str] = Field(None, description="鄉鎮市區")

    lat: float = Field(..., description="緯度")
    lon: float = Field(..., description="經度")
    altitude_m: Optional[float] = Field(None, description="海拔高度 (公尺)")

    observed_at: str = Field(..., description="觀測時間 (ISO 8601 或 YYYY-MM-DD HH:MM:SS)")
    temperature_c: float = Field(..., description="氣溫 (攝氏度)")

    humidity_percent: Optional[float] = Field(None, description="相對濕度 (%)")
    pressure_hpa: Optional[float] = Field(None, description="測站氣壓 (hPa)")
    wind_speed_mps: Optional[float] = Field(None, description="風速 (m/s)")
    wind_direction_deg: Optional[float] = Field(None, description="風向 (度)")
    precipitation_mm: Optional[float] = Field(None, description="累積降雨量 (mm)")
    weather: Optional[str] = Field(None, description="天氣描述")

    # 生活氣象與外出指南新增欄位
    uv_index: Optional[float] = Field(None, description="紫外線指數 (UVI)")
    uv_level: Optional[str] = Field(None, description="紫外線等級 (低量/中量/高量/過量/危險)")
    comfort_text: Optional[str] = Field(None, description="體感舒適度描述")
    dressing_advice: Optional[str] = Field(None, description="建議穿著搭配")
    essentials: Optional[List[str]] = Field(None, description="外出必備推薦小物清單")

class LatestTemperatureResponse(BaseModel):
    source: str = "CWA"
    updated_at: str
    count: int
    stations: List[StationTemperature]

class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [lon, lat]

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]

class GeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class HealthResponse(BaseModel):
    status: str
    cwa_cache_status: str
    latest_cwa_time: Optional[str] = None
    stations_count: int = 0
