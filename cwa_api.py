"""
Phase 1: 資料獲取與解析模組 (cwa_api.py)
負責串接中央氣象署 (CWA) 開放資料 API (F-C0032-001 今明 36 小時天氣預報)
解析 JSON 字典與清單結構，精準萃取「縣市、預報時段、天氣現象、降雨機率、最高溫、最低溫、舒適度」。
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CWA 36小時天氣預報 API 網址
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

# 台灣 22 縣市經緯度對照表 (供 Folium 地圖視覺化定位使用)
TAIWAN_COORDINATES = {
    "臺北市": (25.0330, 121.5654),
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


def fetch_cwa_weather(api_key: str) -> dict:
    """
    發送 HTTP GET 請求至 CWA Open Data API 取得原始 JSON 資料。
    """
    if not api_key:
        raise ValueError("請提供有效的中央氣象署 CWA API Key！")

    params = {
        "Authorization": api_key,
        "format": "JSON"
    }

    try:
        response = requests.get(CWA_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("success") == "true":
            raise RuntimeError(f"CWA API 回傳錯誤: {data.get('message', '未知錯誤')}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"連線中央氣象署 API 失敗: {e}")
        raise


def parse_weather_json(raw_json: dict) -> pd.DataFrame:
    """
    解析 CWA API 的複雜巢狀 JSON 結構 (Dictionary & List)
    精準萃取各縣市、時段、天氣現象(Wx)、降雨機率(PoP)、最低溫(MinT)、最高溫(MaxT)、舒適度(CI)
    """
    records = raw_json.get("records", {}).get("location", [])
    if not records:
        logger.warning("解析 JSON 時未找到 location 節點")
        return pd.DataFrame()

    extracted_rows = []

    for loc in records:
        location_name = loc.get("locationName", "")
        weather_elements = loc.get("weatherElement", [])

        # 將 weatherElement list 轉為 dict 以利快速索引
        element_dict = {elem.get("elementName"): elem.get("time", []) for elem in weather_elements}

        wx_list = element_dict.get("Wx", [])
        pop_list = element_dict.get("PoP", [])
        mint_list = element_dict.get("MinT", [])
        ci_list = element_dict.get("CI", [])
        maxt_list = element_dict.get("MaxT", [])

        time_slots_count = len(wx_list)

        for i in range(time_slots_count):
            start_time = wx_list[i].get("startTime", "")
            end_time = wx_list[i].get("endTime", "")
            weather_desc = wx_list[i].get("parameter", {}).get("parameterName", "多雲")

            pop = int(pop_list[i].get("parameter", {}).get("parameterName", 0)) if i < len(pop_list) else 0
            min_t = int(mint_list[i].get("parameter", {}).get("parameterName", 20)) if i < len(mint_list) else 20
            max_t = int(maxt_list[i].get("parameter", {}).get("parameterName", 28)) if i < len(maxt_list) else 28
            ci = ci_list[i].get("parameter", {}).get("parameterName", "舒適") if i < len(ci_list) else "舒適"

            coords = TAIWAN_COORDINATES.get(location_name, (23.7, 120.9))

            extracted_rows.append({
                "locationName": location_name,
                "startTime": start_time,
                "endTime": end_time,
                "weather": weather_desc,
                "pop": pop,
                "minT": min_t,
                "maxT": max_t,
                "ci": ci,
                "latitude": coords[0],
                "longitude": coords[1]
            })

    df = pd.DataFrame(extracted_rows)
    return df


def generate_mock_weather_data() -> pd.DataFrame:
    """
    提供模擬示範資料 (當使用者尚未取得 API Key 時，系統能立即可視化運行)。
    模擬 22 個縣市、3 個時段的預報數值。
    """
    now = datetime.now()
    t1_start = now.strftime("%Y-%m-%d 12:00:00")
    t1_end = (now + timedelta(hours=6)).strftime("%Y-%m-%d 18:00:00")
    t2_start = (now + timedelta(hours=6)).strftime("%Y-%m-%d 18:00:00")
    t2_end = (now + timedelta(hours=18)).strftime("%Y-%m-%d 06:00:00")
    t3_start = (now + timedelta(hours=18)).strftime("%Y-%m-%d 06:00:00")
    t3_end = (now + timedelta(hours=30)).strftime("%Y-%m-%d 18:00:00")

    periods = [
        (t1_start, t1_end),
        (t2_start, t2_end),
        (t3_start, t3_end)
    ]

    mock_profiles = {
        "臺北市": (24, 30, "多雲短暫陣雨", 30),
        "新北市": (23, 29, "多雲時陰短暫陣雨", 40),
        "基隆市": (23, 28, "陰短暫陣雨", 50),
        "桃園市": (23, 29, "多雲午後短暫雷陣雨", 30),
        "新竹市": (24, 30, "晴時多雲", 10),
        "新竹縣": (23, 29, "晴時多雲", 10),
        "苗栗縣": (23, 30, "晴時多雲", 10),
        "臺中市": (24, 32, "晴朗炎熱", 0),
        "彰化縣": (24, 31, "晴天", 10),
        "南投縣": (22, 30, "多雲午後局部雷陣雨", 30),
        "雲林縣": (24, 31, "晴時多雲", 10),
        "嘉義市": (24, 32, "晴朗", 10),
        "嘉義縣": (24, 31, "晴天", 10),
        "臺南市": (25, 32, "晴天", 10),
        "高雄市": (26, 33, "晴朗炎熱", 10),
        "屏東縣": (25, 33, "多雲局部短暫陣雨", 20),
        "宜蘭縣": (23, 28, "陰有短暫陣雨", 60),
        "花蓮縣": (24, 29, "多雲局部陣雨", 30),
        "臺東縣": (25, 30, "多雲", 20),
        "澎湖縣": (25, 30, "晴時多雲", 0),
        "金門縣": (24, 29, "晴天", 0),
        "連江縣": (22, 26, "陰短暫陣雨", 40),
    }

    rows = []
    for city, (base_min, base_max, weather, pop) in mock_profiles.items():
        coords = TAIWAN_COORDINATES.get(city, (23.7, 120.9))
        for idx, (p_start, p_end) in enumerate(periods):
            min_t = base_min - (1 if idx == 1 else 0)
            max_t = base_max - (2 if idx == 1 else 0) + (1 if idx == 2 else 0)
            rows.append({
                "locationName": city,
                "startTime": p_start,
                "endTime": p_end,
                "weather": weather,
                "pop": pop,
                "minT": min_t,
                "maxT": max_t,
                "ci": "舒適至悶熱" if max_t >= 30 else "舒適",
                "latitude": coords[0],
                "longitude": coords[1]
            })

    return pd.DataFrame(rows)
