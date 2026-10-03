"""
Taiwan Weather Forecast & CWA × Windy 台灣即時氣象平台 (app.py)
整合：
- 🌟 現代化 CWA × Windy / Leaflet 科技地圖 (含紫外線、濕度、建議穿著、出門必帶小物、Top 10 排行與語音播報)
- 📈 36 小時高低溫走勢圖 (Plotly)
- 🗺️ 標準無浮水印台灣地圖 (OpenStreetMap)
- 📊 SQLite 結構化存儲與 CSV 匯出
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import json
import os

from cwa_api import fetch_cwa_weather, parse_weather_json, generate_mock_weather_data, TAIWAN_COORDINATES
from database import (
    init_db, save_forecasts, get_all_forecasts, 
    get_forecasts_by_location, get_forecasts_by_time,
    get_available_locations, get_available_time_slots,
    get_db_stats
)
from backend.app.services.cwa_client import CWAClient

# 1. 頁面基本設定
st.set_page_config(
    page_title="CWA × Windy 台灣即時氣候生活平台",
    page_icon="🇹🇼",
    layout="wide",
    initial_sidebar_state="collapsed"  # 預設收合側邊欄，讓視覺聚焦在現代化全屏地圖
)

DEFAULT_CWA_KEY = os.getenv("CWA_API_KEY", "CWA-8C2E2368-812D-4F61-8F55-8AFC60837532")

# 自訂頂部與全域樣式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans TC', sans-serif;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100%;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 22px;
        font-weight: 700;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)


# 2. 自動確保 SQLite 資料庫就緒
def ensure_database_ready():
    if not os.path.exists("data.db"):
        init_db("data.db")
        try:
            raw_data = fetch_cwa_weather(DEFAULT_CWA_KEY)
            df = parse_weather_json(raw_data)
            save_forecasts(df, "data.db")
        except Exception:
            mock_df = generate_mock_weather_data()
            save_forecasts(mock_df, "data.db")

ensure_database_ready()


# 3. 獲取真實即時測站觀測資料 (含紫外線、穿搭、出門小物)
@st.cache_data(ttl=300)
def get_live_cwa_stations(api_key: str):
    client = CWAClient(api_key)
    stations = client.fetch_observations()
    return [s.model_dump() for s in stations]

stations_data = get_live_cwa_stations(DEFAULT_CWA_KEY)
stations_json_str = json.dumps(stations_data, ensure_ascii=False)


# 4. 側邊欄：API 金鑰與資料庫管理
with st.sidebar:
    st.subheader("🔑 中央氣象署 (CWA) 授權設定")
    api_key_input = st.text_input(
        "CWA API Key 授權碼",
        value=DEFAULT_CWA_KEY,
        type="password"
    )
    if st.button("🔄 同步更新即時氣象", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.success("已發送更新請求！")
        st.rerun()

    st.markdown("---")
    stats = get_db_stats("data.db")
    st.markdown(f"**💾 本地 SQLite 狀態**")
    st.markdown(f"- 記錄總筆數：`{stats['total_records']}` 筆")
    st.markdown(f"- 最後更新：`{stats['last_updated']}`")


# 5. 主畫面分頁
tab_modern, tab_trend, tab_folium, tab_data = st.tabs([
    "🌟 CWA × Windy 科技地圖與生活指南 (推薦)",
    "📈 各縣市 36 小時氣溫趨勢分析",
    "🗺️ 標準台灣氣溫分布地圖",
    "📊 SQLite 完整資料檢視"
])


# =========================================================================
# Tab 1: 使用者最喜愛之【CWA × Windy 現代化全屏科技地圖】(嵌入式獨立組件)
# =========================================================================
with tab_modern:
    modern_component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.4.0/dist/leaflet.css" />
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
      <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', 'Noto Sans TC', sans-serif; }}
        body {{ background: #0b0f19; color: #f8fafc; overflow: hidden; width: 100vw; height: 100vh; }}
        #map {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }}

        /* 頂部導航列 */
        .glass-panel {{
          background: rgba(15, 23, 42, 0.82);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 14px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
          z-index: 1000;
        }}

        .top-navbar {{
          position: absolute;
          top: 14px;
          left: 14px;
          right: 14px;
          height: 58px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 20px;
        }}

        .brand {{ display: flex; align-items: center; gap: 10px; }}
        .brand-badge {{
          display: flex; align-items: center; gap: 8px;
          background: rgba(6, 182, 212, 0.18);
          border: 1px solid rgba(6, 182, 212, 0.35);
          padding: 4px 12px; border-radius: 9999px;
        }}
        .pulse-dot {{
          width: 8px; height: 8px; background-color: #10b981; border-radius: 50%;
          box-shadow: 0 0 8px #10b981; animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
          0% {{ transform: scale(0.95); opacity: 0.8; }}
          70% {{ transform: scale(1.1); opacity: 1; }}
          100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
        .brand-title {{
          font-weight: 700; font-size: 1.05rem;
          background: linear-gradient(135deg, #38bdf8, #818cf8);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .brand-sub {{ font-size: 0.82rem; color: #94a3b8; }}

        .header-actions {{ display: flex; align-items: center; gap: 10px; }}
        .btn {{
          display: inline-flex; align-items: center; gap: 6px;
          padding: 7px 14px; border-radius: 8px; font-size: 0.84rem; font-weight: 600;
          cursor: pointer; border: none; transition: all 0.2s;
        }}
        .btn-glass {{ background: rgba(255, 255, 255, 0.1); color: white; border: 1px solid rgba(255,255,255,0.15); }}
        .btn-glass:hover {{ background: rgba(255, 255, 255, 0.2); transform: translateY(-1px); }}
        .btn-primary {{ background: linear-gradient(135deg, #0284c7, #2563eb); color: white; }}
        .btn-primary:hover {{ background: linear-gradient(135deg, #0369a1, #1d4ed8); transform: translateY(-1px); }}

        /* 右側控制面板 */
        .control-panel {{
          position: absolute; top: 82px; right: 14px; width: 290px; padding: 16px;
        }}
        .panel-title {{ font-size: 0.88rem; font-weight: 700; margin-bottom: 12px; color: #f1f5f9; display: flex; justify-content: space-between; }}
        .section-label {{ font-size: 0.74rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin: 10px 0 6px 0; }}
        .custom-select {{
          width: 100%; background: rgba(0,0,0,0.45); border: 1px solid rgba(255,255,255,0.18);
          color: white; padding: 7px 10px; border-radius: 6px; font-size: 0.82rem; outline: none;
        }}
        .switch-row {{
          display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; margin-top: 8px; cursor: pointer;
        }}

        /* 左下角排行榜 */
        .leaderboard-panel {{
          position: absolute; bottom: 20px; left: 20px; width: 270px; padding: 12px 16px; max-height: 320px;
        }}
        .leaderboard-title {{ font-size: 0.86rem; font-weight: 700; margin-bottom: 8px; color: #f87171; display: flex; align-items: center; gap: 6px; }}
        .ranking-item {{
          display: flex; justify-content: space-between; align-items: center;
          padding: 5px 8px; background: rgba(255, 255, 255, 0.04); border-radius: 4px; font-size: 0.78rem; margin-bottom: 4px; cursor: pointer;
        }}
        .ranking-item:hover {{ background: rgba(255, 255, 255, 0.12); transform: translateX(3px); }}

        /* 右下角氣溫圖例 */
        .legend-panel {{
          position: absolute; bottom: 20px; right: 20px; width: 290px; padding: 10px 14px;
        }}
        .gradient-bar {{
          height: 8px; border-radius: 4px;
          background: linear-gradient(to right, #2b6cb0, #3182ce, #38a169, #ecc94b, #ed8936, #e53e3e, #9b2c2c);
          margin: 6px 0;
        }}
        .legend-labels {{ display: flex; justify-content: space-between; font-size: 0.68rem; color: #94a3b8; }}

        /* 測站標記 Badge */
        .cwa-badge {{
          display: flex; align-items: center; justify-content: center;
          color: white; font-weight: 700; font-size: 11px;
          border-radius: 9999px; border: 1.5px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.5); cursor: pointer;
          transition: transform 0.2s;
        }}
        .cwa-badge:hover {{ transform: scale(1.3) !important; z-index: 1000 !important; }}

        /* Popup 樣式 */
        .leaflet-popup-content-wrapper {{
          background: rgba(15, 23, 42, 0.94) !important;
          backdrop-filter: blur(14px) !important;
          border: 1px solid rgba(255,255,255,0.2) !important;
          border-radius: 12px !important; color: white !important;
        }}
        .leaflet-popup-tip {{ background: rgba(15, 23, 42, 0.94) !important; }}
        .popup-card {{ min-width: 260px; font-size: 0.8rem; }}
        .popup-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
        .popup-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px 8px; margin: 8px 0; color: #cbd5e1; font-size: 0.78rem; }}
        .popup-grid b {{ color: white; }}
        .lifestyle-box {{
          background: rgba(255,255,255,0.05); border-left: 3px solid #06b6d4;
          padding: 6px 8px; border-radius: 4px; font-size: 0.75rem; margin-top: 6px; line-height: 1.35;
        }}
        .essentials-tags {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }}
        .tag {{ background: rgba(6,182,212,0.18); border: 1px solid rgba(6,182,212,0.3); font-size: 0.7rem; padding: 2px 6px; border-radius: 9999px; }}
      </style>
    </head>
    <body>
      <div id="map"></div>

      <!-- 頂部列 -->
      <div class="glass-panel top-navbar">
        <div class="brand">
          <div class="brand-badge">
            <span class="pulse-dot"></span>
            <span class="brand-title">CWA × Windy</span>
          </div>
          <span class="brand-sub">台灣氣象站即時氣溫視覺化</span>
          <div id="obs-time-tag" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); padding: 4px 12px; border-radius: 9999px; font-size: 0.76rem; color: #38bdf8; display: flex; align-items: center; gap: 5px;">
            <span>🕒 測站觀測時間：</span>
            <strong id="top-obs-time">載入中...</strong>
          </div>
        </div>

        <div class="header-actions">
          <button class="btn btn-glass" id="btn-voice">🎙️ 語音播報</button>
          <button class="btn btn-primary" id="btn-sync">🔄 即時同步</button>
        </div>
      </div>

      <!-- 右側控制 -->
      <div class="glass-panel control-panel">
        <div class="panel-title">
          <span>🎛️ 圖層與篩選控制</span>
        </div>
        <div class="section-label">地圖圖資風格 (完全無浮水印)</div>
        <select id="select-tile" class="custom-select">
          <option value="osm">🗺️ 標準道路 (OpenStreetMap - 推薦)</option>
          <option value="esri_dark">🌌 科技深灰 (Esri Dark Gray)</option>
          <option value="satellite">🛰️ 衛星遙測 (Esri Satellite)</option>
        </select>

        <div class="section-label">縣市快速篩選</div>
        <select id="select-county" class="custom-select">
          <option value="全部">全部縣市 (全台灣)</option>
          <option value="臺北市">臺北市</option>
          <option value="新北市">新北市</option>
          <option value="桃園市">桃園市</option>
          <option value="臺中市">臺中市</option>
          <option value="臺南市">臺南市</option>
          <option value="高雄市">高雄市</option>
          <option value="基隆市">基隆市</option>
          <option value="新竹市">新竹市</option>
          <option value="新竹縣">新竹縣</option>
          <option value="苗栗縣">苗栗縣</option>
          <option value="彰化縣">彰化縣</option>
          <option value="南投縣">南投縣</option>
          <option value="雲林縣">雲林縣</option>
          <option value="嘉義市">嘉義市</option>
          <option value="嘉義縣">嘉義縣</option>
          <option value="屏東縣">屏東縣</option>
          <option value="宜蘭縣">宜蘭縣</option>
          <option value="花蓮縣">花蓮縣</option>
          <option value="臺東縣">臺東縣</option>
          <option value="澎湖縣">澎湖縣</option>
          <option value="金門縣">金門縣</option>
          <option value="連江縣">連江縣</option>
        </select>

        <label class="switch-row" style="color: #facc15; margin-top: 10px;">
          <span>⛰️ 排除高山測站 (&gt;1000m)</span>
          <input type="checkbox" id="toggle-mountain">
        </label>
      </div>

      <!-- 左下角排行榜 -->
      <div class="glass-panel leaderboard-panel">
        <div class="leaderboard-title">🔥 全台 Top 10 最高溫測站</div>
        <div id="ranking-list"></div>
      </div>

      <!-- 右下角圖例 -->
      <div class="glass-panel legend-panel">
        <div style="font-size:0.74rem; font-weight:700; color:#94a3b8;">氣溫色階 (°C)</div>
        <div class="gradient-bar"></div>
        <div class="legend-labels">
          <span>&lt;10° 寒</span>
          <span>15° 涼</span>
          <span>20° 溫</span>
          <span>25° 舒</span>
          <span>30° 熱</span>
          <span>&gt;35° 酷熱</span>
        </div>
      </div>

      <script src="https://unpkg.com/leaflet@1.4.0/dist/leaflet.js"></script>
      <script>
        const stations = {stations_json_str};

        // 7 階氣溫色碼表
        function getColor(temp) {{
          if (temp < 10) return "#2b6cb0";
          if (temp < 15) return "#3182ce";
          if (temp < 20) return "#38a169";
          if (temp < 25) return "#ecc94b";
          if (temp < 30) return "#ed8936";
          if (temp < 35) return "#e53e3e";
          return "#9b2c2c";
        }}

        // 初始化 Leaflet 地圖 (以台灣為中心，預設完全無浮水印的 OpenStreetMap)
        const map = L.map('map', {{
          center: [23.7, 120.95],
          zoom: 7.6,
          zoomControl: false
        }});
        L.control.zoom({{ position: 'bottomright' }}).addTo(map);

        let currentTile = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
          attribution: '&copy; OpenStreetMap contributors &copy; CWA',
          maxZoom: 18
        }}).addTo(map);

        const markersLayer = L.layerGroup().addTo(map);

        // 圖資切換
        document.getElementById('select-tile').addEventListener('change', (e) => {{
          map.removeLayer(currentTile);
          const val = e.target.value;
          if (val === 'esri_dark') {{
            currentTile = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ maxZoom: 18 }}).addTo(map);
          }} else if (val === 'satellite') {{
            currentTile = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ maxZoom: 18 }}).addTo(map);
          }} else {{
            currentTile = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 18 }}).addTo(map);
          }}
        }});

        // 渲染測站標記
        function renderMarkers() {{
          markersLayer.clearLayers();
          const county = document.getElementById('select-county').value;
          const excludeMtn = document.getElementById('toggle-mountain').checked;

          const filtered = stations.filter(st => {{
            if (county !== '全部' && st.county !== county) return false;
            if (excludeMtn && st.altitude_m && st.altitude_m > 1000) return false;
            return true;
          }});

          filtered.forEach(st => {{
            const color = getColor(st.temperature_c);
            const iconHtml = `<div class="cwa-badge" style="background:${{color}}; width:32px; height:32px;">${{Math.round(st.temperature_c)}}°</div>`;

            const marker = L.marker([st.lat, st.lon], {{
              icon: L.divIcon({{
                className: 'custom-icon',
                html: iconHtml,
                iconSize: [32, 32],
                iconAnchor: [16, 16]
              }})
            }});

            const itemsHtml = (st.essentials || ['☔ 晴雨傘', '🧴 防曬乳', '💧 隨身水瓶'])
              .map(it => `<span class="tag">${{it}}</span>`).join('');

            const obsTimeDisplay = st.observed_at ? st.observed_at.replace('T', ' ').substring(0, 16) : '即時觀測';

            const popupHtml = `
              <div class="popup-card">
                <div class="popup-header">
                  <h4 style="color:#38bdf8; margin:0;">${{st.station_name}}</h4>
                  <span style="background:${{color}}; color:white; padding:2px 8px; border-radius:10px; font-weight:bold;">${{st.temperature_c.toFixed(1)}}°C</span>
                </div>
                <div style="color:#94a3b8; font-size:11px;">${{st.county || ''}} ${{st.town || ''}} (測站: ${{st.station_id}})</div>
                <div style="color:#38bdf8; font-size:11px; margin:2px 0 4px 0; font-weight:600;">🕒 測站觀測時間：${{obsTimeDisplay}}</div>
                <div class="popup-grid">
                  <div>天氣：<b>${{st.weather || '多雲'}}</b></div>
                  <div>濕度：<b>${{st.humidity_percent || 65}}%</b></div>
                  <div>風速：<b>${{st.wind_speed_mps || 2.5}} m/s</b></div>
                  <div>雨量：<b>${{st.precipitation_mm || 0}} mm</b></div>
                  <div>海拔：<b>${{st.altitude_m ? Math.round(st.altitude_m) + ' m' : '15 m'}}</b></div>
                </div>
                <div style="color:#38bdf8; font-weight:bold; font-size:11px; margin-top:6px;">☀️ 紫外線：${{st.uv_level || '中量級'}} | 💧 ${{st.comfort_text || '舒適'}}</div>
                <div class="lifestyle-box">👕 <b>建議穿著：</b>${{st.dressing_advice || '舒適通風短袖服裝'}}</div>
                <div style="font-size:11px; color:#94a3b8; margin-top:6px;">🎒 <b>出門必備推薦：</b></div>
                <div class="essentials-tags">${{itemsHtml}}</div>
              </div>
            `;
            marker.bindPopup(popupHtml, {{ maxWidth: 300 }});
            marker.addTo(markersLayer);
          }});
        }}

        // 更新頂部觀測時間
        if (stations.length > 0 && stations[0].observed_at) {{
          const timeStr = stations[0].observed_at.replace('T', ' ').substring(0, 16);
          const topTimeEl = document.getElementById('top-obs-time');
          if (topTimeEl) topTimeEl.innerText = timeStr;
        }} else {{
          const nowStr = new Date().toLocaleString('zh-TW', {{ hour12: false }}).substring(0, 16);
          const topTimeEl = document.getElementById('top-obs-time');
          if (topTimeEl) topTimeEl.innerText = nowStr;
        }}

        // 渲染排行榜
        function renderLeaderboard() {{
          const listEl = document.getElementById('ranking-list');
          listEl.innerHTML = '';
          const sorted = [...stations].sort((a,b) => b.temperature_c - a.temperature_c).slice(0, 10);
          sorted.forEach((st, idx) => {{
            const div = document.createElement('div');
            div.className = 'ranking-item';
            div.innerHTML = `
              <div><b style="color:${{idx < 3 ? '#ef4444' : '#94a3b8'}}">#${{idx+1}}</b> ${{st.station_name}} <span style="color:#64748b; font-size:11px;">(${{st.county || ''}})</span></div>
              <b style="color:#f87171;">${{st.temperature_c.toFixed(1)}}°C</b>
            `;
            div.addEventListener('click', () => {{
              map.flyTo([st.lat, st.lon], 11, {{ duration: 1.2 }});
            }});
            listEl.appendChild(div);
          }});
        }}

        // 語音播報
        document.getElementById('btn-voice').addEventListener('click', () => {{
          if (!('speechSynthesis' in window)) return alert('瀏覽器不支援語音播報');
          const sorted = [...stations].sort((a,b) => b.temperature_c - a.temperature_c);
          const hot = sorted[0];
          const text = `中央氣象署即時天氣生活播報。目前全台最高溫出現在 ${{hot.county || ''}}${{hot.station_name}}，氣溫高達 ${{hot.temperature_c.toFixed(1)}} 度。今日紫外線強度為${{hot.uv_level || '中偏高'}}。穿搭建議：${{hot.dressing_advice || '輕便短袖'}}。外出請多補充水分並注意攜帶防曬用品！`;
          window.speechSynthesis.cancel();
          const u = new SpeechSynthesisUtterance(text);
          u.lang = 'zh-TW';
          window.speechSynthesis.speak(u);
        }});

        document.getElementById('btn-sync').addEventListener('click', () => {{
          window.location.reload();
        }});

        document.getElementById('select-county').addEventListener('change', renderMarkers);
        document.getElementById('toggle-mountain').addEventListener('change', renderMarkers);

        renderMarkers();
        renderLeaderboard();
      </script>
    </body>
    </html>
    """

    st.components.v1.html(modern_component_html, height=840, scrolling=False)


# =========================================================================
# Tab 2: 各縣市 36 小時氣溫趨勢分析與生活指南
# =========================================================================
with tab_trend:
    st.subheader("📈 縣市 36 小時氣溫趨勢與生活指南")
    locations = get_available_locations("data.db") or ["臺北市"]
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_city = st.selectbox("請選擇查詢縣市：", options=locations, index=0)

    city_df = get_forecasts_by_location(selected_city, "data.db")
    if not city_df.empty:
        latest_row = city_df.iloc[0]
        start_t = latest_row['startTime'].replace('T', ' ')
        end_t = latest_row['endTime'].replace('T', ' ')
        updated_t = latest_row['updatedAt'] if 'updatedAt' in latest_row else '即時連線'
        st.info(f"🕒 **當前預報區間時間**：`{start_t}` 至 `{end_t}` ｜ **資料庫記錄時間**：`{updated_t}`")

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("即時預報天氣", f"{latest_row['weather']}")
        with c2: st.metric("預測最高溫", f"{city_df['maxT'].max()} °C")
        with c3: st.metric("預測最低溫", f"{city_df['minT'].min()} °C")
        with c4: st.metric("降雨機率", f"{city_df['pop'].max()} %")

        # Plotly 趨勢折線圖
        time_labels = [f"{r['startTime'][5:16]}\n~{r['endTime'][11:16]}" for _, r in city_df.iterrows()]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time_labels, y=city_df['maxT'], mode='lines+markers+text', name='最高溫 (°C)', text=[f"{t}°C" for t in city_df['maxT']], textposition='top center', line=dict(color='#ef4444', width=3)))
        fig.add_trace(go.Scatter(x=time_labels, y=city_df['minT'], mode='lines+markers+text', name='最低溫 (°C)', text=[f"{t}°C" for t in city_df['minT']], textposition='bottom center', line=dict(color='#3b82f6', width=3), fill='tonexty', fillcolor='rgba(239, 68, 68, 0.08)'))
        fig.update_layout(title=f"<b>{selected_city} 未來 36 小時氣溫走勢</b>", template="plotly_white", margin=dict(l=40, r=40, t=50, b=40))
        st.plotly_chart(fig, use_container_width=True)

        # 生活穿搭指南
        st.markdown("##### 🎒 今日生活穿搭與外出小物指南")
        l1, l2 = st.columns(2)
        with l1:
            st.info(f"☀️ **紫外線等級**：高量級\n\n💧 **體感舒適度**：{latest_row['ci']}\n\n👕 **建議穿著**：透氣排汗短袖、舒適棉麻長短褲，進出冷氣房攜帶薄外套。")
        with l2:
            st.success("🎒 **出門必帶推薦小物**：\n- ☔ 折疊晴雨傘\n- 🧴 高係數防曬乳 (SPF50+)\n- 💧 隨身環保水瓶 (隨時補水)\n- 💳 悠遊卡與電子支付")


# =========================================================================
# Tab 3: 標準台灣氣溫分布地圖 (完全無浮水印的 OpenStreetMap)
# =========================================================================
with tab_folium:
    st.subheader("🗺️ 全台氣溫分布地圖 (標準無浮水印 OpenStreetMap)")
    time_slots = get_available_time_slots("data.db")
    if time_slots:
        st.caption(f"🕒 **當前地圖顯示預報時段**：`{time_slots[0][0].replace('T', ' ')}` 至 `{time_slots[0][1].replace('T', ' ')}`")
        slot_df = get_forecasts_by_time(time_slots[0][0], "data.db")
        taiwan_map = folium.Map(location=[23.7, 120.9], zoom_start=7.4, tiles="OpenStreetMap")
        for _, row in slot_df.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=12,
                color="white",
                weight=2,
                fill=True,
                fill_color="#ef4444" if row['maxT'] >= 30 else "#f59e0b",
                fill_opacity=0.85,
                popup=f"{row['locationName']}: {row['weather']} ({row['minT']}°C ~ {row['maxT']}°C)"
            ).add_to(taiwan_map)
        st_folium(taiwan_map, width="100%", height=500)


# =========================================================================
# Tab 4: SQLite 資料庫檢視
# =========================================================================
with tab_data:
    st.subheader("📊 SQLite (data.db) 完整氣象數據表")
    st.caption("💡 包含全台 22 縣市預報時段起訖時間 (startTime / endTime) 與資料寫入時間戳記 (updatedAt)：")
    all_df = get_all_forecasts("data.db")
    if not all_df.empty:
        st.dataframe(all_df, use_container_width=True, hide_index=True)
