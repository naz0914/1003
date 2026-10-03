import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from backend.app.config import settings
from backend.app.schemas.temperature import StationTemperature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INVALID_VALUES = {"", "X", "NA", "null", None, "-99", "-999", "-998", "-99.0", "-999.0"}

COUNTY_COORDS = {
    "臺北市": (25.0377, 121.5149),
    "新北市": (25.0118, 121.4627),
    "基隆市": (25.1276, 121.7392),
    "桃園市": (24.9936, 121.3010),
    "新竹市": (24.8138, 120.9675),
    "新竹縣": (24.8387, 121.0177),
    "苗栗縣": (24.5602, 120.8214),
    "臺中市": (24.1477, 120.6736),
    "彰化縣": (24.0518, 120.5161),
    "南投縣": (23.9610, 120.9719),
    "雲林縣": (23.7092, 120.4313),
    "嘉義市": (23.4800, 120.4491),
    "嘉義縣": (23.4518, 120.2555),
    "臺南市": (22.9997, 120.2270),
    "高雄市": (22.6273, 120.3014),
    "屏東縣": (22.6828, 120.4879),
    "宜蘭縣": (24.7021, 121.7377),
    "花蓮縣": (23.9872, 121.6016),
    "臺東縣": (22.7583, 121.1444),
    "澎湖縣": (23.5712, 119.5793),
    "金門縣": (24.4493, 118.3766),
    "連江縣": (26.1558, 119.9519),
}


def parse_float(val: Any) -> Optional[float]:
    if val in INVALID_VALUES or val is None:
        return None
    try:
        f = float(val)
        return None if f in {-99.0, -999.0, -998.0} else f
    except (ValueError, TypeError):
        return None


def calculate_lifestyle_guide(temp: float, rh: Optional[float], precip: Optional[float], wx: Optional[str], wind: Optional[float]) -> Tuple[float, str, str, str, List[str]]:
    """計算紫外線、濕度舒適度、穿著建議與外出必帶小物清單"""
    rh_val = rh if rh is not None else 65.0
    precip_val = precip if precip is not None else 0.0
    wx_str = wx or "多雲"
    wind_val = wind if wind is not None else 2.0

    # 1. 紫外線估算 (UV Index & Level)
    if "晴" in wx_str:
        uvi = 8.5
        uv_level = "過量級 (UVI 8-10)"
    elif "多雲" in wx_str:
        uvi = 5.2
        uv_level = "中量級 (UVI 3-5)"
    elif "陰" in wx_str:
        uvi = 3.0
        uv_level = "中量級 (UVI 3-5)"
    else:
        uvi = 1.8
        uv_level = "低量級 (UVI 0-2)"

    # 2. 濕度與體感舒適度 (Humidity & Comfort)
    if rh_val >= 80:
        comfort = f"濕度 {rh_val:.0f}% 偏高：悶熱潮濕易出汗" if temp >= 28 else f"濕度 {rh_val:.0f}%：陰涼潮濕感明顯"
    elif rh_val >= 60:
        comfort = f"濕度 {rh_val:.0f}%：體感適中略顯溫暖" if temp >= 28 else f"濕度 {rh_val:.0f}%：體感舒適宜人"
    elif rh_val >= 40:
        comfort = f"濕度 {rh_val:.0f}%：乾爽通風宜人"
    else:
        comfort = f"濕度 {rh_val:.0f}%：空氣偏乾燥，注意補水保濕"

    # 3. 建議穿著 (Dressing Advice)
    if temp >= 32:
        dressing = "酷熱炎夏：排汗短袖、無袖涼感背心、透氣棉麻短褲，避免深色厚重衣物"
    elif temp >= 28:
        dressing = "溫熱夏季：短袖 T-Shirt、涼爽棉質短褲或薄長褲，搭配透氣透汗材質"
    elif temp >= 24:
        dressing = "舒適宜人：純棉短袖搭休閒長褲，進出冷氣房建議隨身攜帶輕薄罩衫"
    elif temp >= 20:
        dressing = "微涼舒適：薄長袖、針織上衣搭休閒長褲，早晚加件防風休閒外套"
    elif temp >= 15:
        dressing = "偏涼秋意：長袖長褲、厚棉衛衣、休閒夾克風衣，留意日夜溫差"
    else:
        dressing = "寒冷冬溫：發熱保暖內搭、厚毛衣、羽絨保暖大衣，搭配防風圍巾"

    # 4. 外出必帶推薦小物 (Essentials)
    essentials = []
    if precip_val > 0 or any(k in wx_str for k in ["雨", "雷", "陣"]):
        essentials.append("☔ 折疊雨傘 / 輕便雨具")
    if uvi >= 5:
        essentials.append("🧴 高係數防曬乳 (SPF50+)")
        essentials.append("🕶️ 抗UV太陽眼鏡")
        essentials.append("🧢 遮陽帽 / 晴雨傘")
    if temp >= 28:
        essentials.append("💧 隨身保冷環保水瓶 (隨時補水)")
        essentials.append("🪭 手持隨身涼風扇 / 涼感濕紙巾")
    if temp >= 25:
        essentials.append("🧥 冷氣房防著涼薄外套")
    elif temp < 20:
        essentials.append("🧣 保暖圍巾 / 隨身暖暖包")
    if rh_val >= 70 or temp >= 28:
        essentials.append("🧻 吸汗手帕 / 面紙")

    essentials.append("💳 悠遊卡與電子支付")

    return uvi, uv_level, comfort, dressing, essentials


class CWAClient:
    """中央氣象署 (CWA) 多層級資料抓取與解析客戶端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.CWA_API_KEY

    def fetch_observations(self) -> List[StationTemperature]:
        api_key = self.api_key.strip() if self.api_key else ""
        if not api_key:
            logger.warning("未設定 CWA API Key，載入示範測站資料庫")
            return self._generate_mock_stations()

        headers = {
            "Authorization": api_key,
            "User-Agent": "CWA-Weather-Dashboard/1.0"
        }
        params = {
            "Authorization": api_key,
            "format": "JSON"
        }

        # 1. 優先嘗試 O-A0001-001 (局屬有人氣象站)
        try:
            url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"
            resp = requests.get(url, headers=headers, params=params, timeout=12)
            if resp.status_code == 200:
                stations = self._parse_station_records(resp.json())
                if stations:
                    logger.info(f"✅ 成功從 CWA O-A0001-001 取得 {len(stations)} 個真實測站！")
                    return stations
        except Exception as e:
            logger.warning(f"連線 O-A0001-001 異常: {e}")

        # 2. 次選嘗試 O-A0003-001 (自動氣象站)
        try:
            url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"
            resp = requests.get(url, headers=headers, params=params, timeout=12)
            if resp.status_code == 200:
                stations = self._parse_station_records(resp.json())
                if stations:
                    logger.info(f"✅ 成功從 CWA O-A0003-001 取得 {len(stations)} 個真實測站！")
                    return stations
        except Exception as e:
            logger.warning(f"連線 O-A0003-001 異常: {e}")

        # 3. 備選嘗試 F-C0032-001
        try:
            url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
            resp = requests.get(url, headers=headers, params=params, timeout=12)
            if resp.status_code == 200:
                stations = self._parse_fc0032_records(resp.json())
                if stations:
                    logger.info(f"✅ 成功從 CWA F-C0032-001 取得 {len(stations)} 縣市真實即時氣象！")
                    return stations
        except Exception as e:
            logger.warning(f"連線 F-C0032-001 異常: {e}")

        return self._generate_mock_stations()

    def _parse_station_records(self, data: dict) -> List[StationTemperature]:
        records = data.get("records", {})
        station_list = records.get("Station", []) or records.get("location", [])
        valid_stations: List[StationTemperature] = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in station_list:
            station_id = item.get("StationId") or item.get("stationId")
            station_name = item.get("StationName") or item.get("locationName")
            if not station_id or not station_name:
                continue

            geo_info = item.get("GeoInfo", {})
            county = geo_info.get("CountyName") or item.get("parameter", {}).get("COUNTY") or item.get("county")
            town = geo_info.get("TownName") or item.get("parameter", {}).get("TOWN") or item.get("town")
            altitude_m = parse_float(geo_info.get("StationAltitude") or item.get("altitude"))

            lat = None
            lon = None
            if "Coordinates" in geo_info:
                for coord in geo_info["Coordinates"]:
                    if coord.get("CoordinateName") == "WGS84":
                        lat = parse_float(coord.get("CoordinateLatitude"))
                        lon = parse_float(coord.get("CoordinateLongitude"))
            if lat is None:
                lat = parse_float(item.get("StationLatitude") or item.get("lat"))
                lon = parse_float(item.get("StationLongitude") or item.get("lon"))

            if lat is None or lon is None:
                if county in COUNTY_COORDS:
                    lat, lon = COUNTY_COORDS[county]
                else:
                    continue

            obs_time = item.get("ObsTime", {}).get("DateTime") or item.get("time", {}).get("obsTime") or now_str

            weather_elem = item.get("WeatherElement", {})
            if isinstance(weather_elem, list):
                weather_dict = {el.get("elementName"): el.get("elementValue") for el in weather_elem}
            else:
                weather_dict = weather_elem

            temp_c = parse_float(weather_dict.get("AirTemperature"))
            if temp_c is None or temp_c < -20.0 or temp_c > 50.0:
                continue

            humidity = parse_float(weather_dict.get("RelativeHumidity"))
            pressure = parse_float(weather_dict.get("AirPressure"))
            wind_speed = parse_float(weather_dict.get("WindSpeed"))
            wind_dir = parse_float(weather_dict.get("WindDirection"))

            precip = None
            now_dict = weather_dict.get("Now", {})
            if isinstance(now_dict, dict):
                precip = parse_float(now_dict.get("Precipitation"))
            if precip is None:
                precip = parse_float(weather_dict.get("Precipitation") or weather_dict.get("DailyPrecipitation") or 0.0)

            weather_desc = weather_dict.get("Weather") if isinstance(weather_dict.get("Weather"), str) else "多雲"

            # 計算生活與穿著指南
            uvi, uv_lvl, comfort, dressing, essentials = calculate_lifestyle_guide(
                temp_c, humidity, precip, weather_desc, wind_speed
            )

            valid_stations.append(StationTemperature(
                station_id=station_id,
                station_name=station_name,
                county=county,
                town=town,
                lat=lat,
                lon=lon,
                altitude_m=altitude_m,
                observed_at=obs_time,
                temperature_c=temp_c,
                humidity_percent=humidity,
                pressure_hpa=pressure,
                wind_speed_mps=wind_speed,
                wind_direction_deg=wind_dir,
                precipitation_mm=precip,
                weather=weather_desc,
                uv_index=uvi,
                uv_level=uv_lvl,
                comfort_text=comfort,
                dressing_advice=dressing,
                essentials=essentials
            ))

        return valid_stations

    def _parse_fc0032_records(self, data: dict) -> List[StationTemperature]:
        records = data.get("records", {}).get("location", [])
        valid = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for loc in records:
            name = loc.get("locationName", "")
            elements = {el.get("elementName"): el.get("time", []) for el in loc.get("weatherElement", [])}
            coords = COUNTY_COORDS.get(name, (23.7, 120.9))

            mint_times = elements.get("MinT", [])
            maxt_times = elements.get("MaxT", [])
            wx_times = elements.get("Wx", [])
            pop_times = elements.get("PoP", [])

            min_t = float(mint_times[0]["parameter"]["parameterName"]) if mint_times else 25.0
            max_t = float(maxt_times[0]["parameter"]["parameterName"]) if maxt_times else 30.0
            temp_avg = round((min_t + max_t) / 2.0, 1)
            wx = wx_times[0]["parameter"]["parameterName"] if wx_times else "多雲"
            pop = float(pop_times[0]["parameter"]["parameterName"]) if pop_times else 0.0
            obs_time = wx_times[0].get("startTime", now_str) if wx_times else now_str

            uvi, uv_lvl, comfort, dressing, essentials = calculate_lifestyle_guide(
                temp_avg, 65.0, pop, wx, 2.4
            )

            valid.append(StationTemperature(
                station_id=f"CWA_{name}",
                station_name=name,
                county=name,
                town="中心測點",
                lat=coords[0],
                lon=coords[1],
                altitude_m=15.0,
                observed_at=obs_time,
                temperature_c=temp_avg,
                humidity_percent=65.0,
                pressure_hpa=1012.0,
                wind_speed_mps=2.4,
                precipitation_mm=pop,
                weather=wx,
                uv_index=uvi,
                uv_level=uv_lvl,
                comfort_text=comfort,
                dressing_advice=dressing,
                essentials=essentials
            ))
        return valid

    def _generate_mock_stations(self) -> List[StationTemperature]:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:00")
        mock_data = [
            ("466920", "臺北", "臺北市", "中正區", 25.0377, 121.5149, 31.4, 68, 1011.5, 2.3, 0.0, "多雲"),
            ("466910", "鞍部", "臺北市", "北投區", 25.1826, 121.5297, 22.8, 88, 920.1, 4.1, 0.5, "陰有霧"),
            ("466930", "竹子湖", "臺北市", "北投區", 25.1621, 121.5445, 24.2, 85, 942.3, 3.2, 0.0, "陰天"),
            ("466900", "淡水", "新北市", "淡水區", 25.1649, 121.4489, 29.5, 72, 1012.0, 3.5, 0.0, "多雲時晴"),
            ("466880", "板橋", "新北市", "板橋區", 25.0000, 121.4422, 31.8, 65, 1011.8, 1.8, 0.0, "晴天"),
            ("466940", "基隆", "基隆市", "仁愛區", 25.1333, 121.7405, 28.6, 76, 1012.3, 4.2, 1.0, "短暫雨"),
            ("C0C480", "桃園", "桃園市", "桃園區", 24.9961, 121.3129, 30.2, 70, 1010.8, 2.6, 0.0, "多雲"),
            ("467570", "新竹", "新竹縣", "竹北市", 24.8280, 121.0142, 29.8, 68, 1011.2, 3.8, 0.0, "晴時多雲"),
            ("C0D580", "新竹市", "新竹市", "東區", 24.8055, 120.9734, 30.1, 67, 1011.0, 3.1, 0.0, "晴時多雲"),
            ("C0E750", "苗栗", "苗栗縣", "苗栗市", 24.5650, 120.8256, 31.0, 66, 1011.5, 2.0, 0.0, "晴天"),
            ("467490", "臺中", "臺中市", "北區", 24.1458, 120.6840, 32.5, 62, 1010.5, 1.9, 0.0, "晴朗炎熱"),
            ("C0F970", "大甲", "臺中市", "大甲區", 24.3468, 120.6213, 31.2, 65, 1011.1, 3.4, 0.0, "晴天"),
            ("C0G620", "彰化", "彰化縣", "彰化市", 24.0754, 120.5583, 32.0, 64, 1010.8, 2.2, 0.0, "晴朗"),
            ("C0H990", "南投", "南投縣", "南投市", 23.9103, 120.6859, 31.5, 66, 1010.2, 1.5, 0.0, "多雲"),
            ("467650", "日月潭", "南投縣", "魚池鄉", 23.8814, 120.9081, 25.4, 78, 898.5, 1.8, 0.0, "舒適多雲"),
            ("467550", "玉山", "南投縣", "信義鄉", 23.4876, 120.9595, 8.5, 82, 642.0, 5.5, 0.0, "晴朗酷寒"),
            ("467530", "阿里山", "嘉義縣", "阿里山鄉", 23.5082, 120.8132, 15.2, 80, 775.2, 2.4, 0.0, "涼爽多雲"),
            ("C0K240", "斗六", "雲林縣", "斗六市", 23.7081, 120.5439, 32.3, 63, 1010.6, 2.0, 0.0, "晴天"),
            ("467480", "嘉義", "嘉義市", "西區", 23.4959, 120.4329, 32.8, 62, 1010.4, 2.1, 0.0, "晴朗炎熱"),
            ("467410", "臺南", "臺南市", "中西區", 22.9933, 120.2038, 33.2, 64, 1010.2, 2.5, 0.0, "晴朗炎熱"),
            ("C0X190", "安平", "臺南市", "安平區", 22.9980, 120.1530, 32.6, 68, 1010.5, 3.2, 0.0, "晴天"),
            ("467440", "高雄", "高雄市", "前鎮區", 22.5660, 120.3158, 33.6, 65, 1010.0, 2.8, 0.0, "晴朗炎熱"),
            ("C0V730", "美濃", "高雄市", "美濃區", 22.8983, 120.5367, 34.2, 60, 1009.8, 1.6, 0.0, "酷熱晴朗"),
            ("467590", "恆春", "屏東縣", "恆春鎮", 22.0039, 120.7463, 31.6, 75, 1010.8, 6.2, 0.0, "晴天風大"),
            ("C0R140", "屏東", "屏東縣", "屏東市", 22.6731, 120.4881, 33.8, 62, 1009.9, 2.1, 0.0, "炎熱晴天"),
            ("467080", "宜蘭", "宜蘭縣", "宜蘭市", 24.7640, 121.7565, 28.2, 78, 1011.8, 2.4, 2.5, "短暫陣雨"),
            ("467100", "蘇澳", "宜蘭縣", "蘇澳鎮", 24.5967, 121.8574, 27.8, 80, 1012.0, 3.6, 3.0, "局部陣雨"),
            ("466990", "花蓮", "花蓮縣", "花蓮市", 23.9752, 121.6133, 29.4, 74, 1011.5, 3.1, 0.5, "多雲偶雨"),
            ("C0T820", "玉里", "花蓮縣", "玉里鎮", 23.3364, 121.3128, 31.0, 68, 1010.9, 1.8, 0.0, "多雲時晴"),
            ("467660", "臺東", "臺東縣", "臺東市", 22.7554, 121.1546, 30.6, 72, 1011.2, 3.5, 0.0, "多雲時晴"),
            ("467610", "成功", "臺東縣", "成功鎮", 23.0975, 121.3736, 29.8, 75, 1011.6, 4.0, 0.0, "多雲"),
            ("467620", "蘭嶼", "臺東縣", "蘭嶼鄉", 22.0370, 121.5583, 27.2, 85, 975.3, 7.8, 1.5, "短暫雨"),
            ("467350", "澎湖", "澎湖縣", "馬公市", 23.5655, 119.5631, 30.4, 72, 1011.2, 5.2, 0.0, "晴天風大"),
            ("467110", "金門", "金門縣", "金城鎮", 24.4073, 118.2893, 29.6, 68, 1011.8, 3.8, 0.0, "晴朗"),
            ("467990", "馬祖", "連江縣", "南竿鄉", 26.1691, 119.9230, 26.5, 82, 1012.5, 4.5, 0.0, "多雲時陰"),
        ]
        result = []
        for sid, name, county, town, lat, lon, temp, rh, p, ws, prep, wx in mock_data:
            uvi, uv_lvl, comfort, dressing, essentials = calculate_lifestyle_guide(temp, rh, prep, wx, ws)
            result.append(StationTemperature(
                station_id=sid,
                station_name=name,
                county=county,
                town=town,
                lat=lat,
                lon=lon,
                altitude_m=10.0,
                observed_at=now_str,
                temperature_c=temp,
                humidity_percent=rh,
                pressure_hpa=p,
                wind_speed_mps=ws,
                precipitation_mm=prep,
                weather=wx,
                uv_index=uvi,
                uv_level=uv_lvl,
                comfort_text=comfort,
                dressing_advice=dressing,
                essentials=essentials
            ))
        return result
