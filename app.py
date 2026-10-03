"""
Phase 3 & 4: Streamlit 互動式儀表板主程式 (app.py)
整合 Taiwan Weather Dashboard:
- Step 11~16: Streamlit 介面、下拉選單、折線圖、資料表格
- Step 17~20: Folium 台灣氣溫互動地圖、時段切換、成果整合與效能快取
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import os

from cwa_api import fetch_cwa_weather, parse_weather_json, generate_mock_weather_data, TAIWAN_COORDINATES
from database import (
    init_db, save_forecasts, get_all_forecasts, 
    get_forecasts_by_location, get_forecasts_by_time,
    get_available_locations, get_available_time_slots,
    get_db_stats
)

# 1. 頁面基本設定 (Step 11 & 16)
st.set_page_config(
    page_title="Taiwan Weather Dashboard - 台灣氣象預報儀表板",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂 CSS 提升視覺美感與質感
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(240, 246, 255, 0.8));
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(226, 232, 240, 0.8);
        text-align: center;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-title {
        font-size: 0.88rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #0ea5e9;
        margin-top: 4px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# 2. 自動確保資料庫內有資料 (若初次啟動無資料庫，自動串接即時或示範資料)
DEFAULT_CWA_KEY = os.getenv("CWA_API_KEY", "CWA-8C2E2368-812D-4F61-8F55-8AFC60837532")

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


# 3. 側邊欄：API Key 設定、資料同步與狀態 (Step 3 & 4)
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1590552515252-3a5a1bce7bed?w=600&auto=format&fit=crop&q=80", use_container_width=True)
    st.title("⛅ 天氣儀表板控制台")
    st.caption("基於中央氣象署 (CWA) 開放資料與 SQLite 打造")

    st.markdown("---")
    st.subheader("🔑 CWA API 設定")
    api_key_input = st.text_input(
        "中央氣象署 API Key (授權碼)",
        value=DEFAULT_CWA_KEY,
        type="password",
        placeholder="請輸入 CWA-XXXXXX...",
        help="前往 opendata.cwa.gov.tw 註冊會員即可免費取得 API Key"
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        sync_button = st.button("🔄 同步即時資料", use_container_width=True, type="primary")
    with col_btn2:
        mock_button = st.button("📦 載入示範資料", use_container_width=True)

    # 執行資料同步
    if sync_button:
        if not api_key_input:
            st.error("請先輸入中央氣象署 API Key！若無 Key 可點選「載入示範資料」。")
        else:
            with st.spinner("正在連線中央氣象署 API 取得即時資料..."):
                try:
                    raw_data = fetch_cwa_weather(api_key_input.strip())
                    parsed_df = parse_weather_json(raw_data)
                    count = save_forecasts(parsed_df, "data.db")
                    st.success(f"同步成功！已更新 {count} 筆即時氣象紀錄。")
                    st.rerun()
                except Exception as e:
                    st.error(f"資料抓取失敗: {e}")

    if mock_button:
        with st.spinner("正在載入 22 縣市完整模擬氣象資料..."):
            mock_df = generate_mock_weather_data()
            count = save_forecasts(mock_df, "data.db")
            st.success(f"已成功載入 {count} 筆示範預報資料！")
            st.rerun()

    st.markdown("---")
    stats = get_db_stats("data.db")
    st.markdown(f"**💾 資料庫狀態**")
    st.markdown(f"- 儲存庫：`SQLite (data.db)`")
    st.markdown(f"- 總筆數：`{stats['total_records']}` 筆")
    st.markdown(f"- 最後更新：`{stats['last_updated']}`")

    st.markdown("---")
    st.caption("✨ 專案架構：Python x CWA API x Pandas x SQLite x Streamlit x Folium")


# 4. 主畫面標題區 (Step 16)
st.title("🇹🇼 Taiwan Weather Dashboard 台灣氣象預報儀表板")
st.markdown("透過 **中央氣象署開放資料 (CWA)** 即時串接全台 22 縣市未來 36 小時天氣預報，包含溫度分布地圖、高低溫走勢與歷史查詢。")

# 5. 取得現有時段與縣市
time_slots = get_available_time_slots("data.db")
locations = get_available_locations("data.db")

if not time_slots or not locations:
    st.warning("⚠️ 目前資料庫尚無預報資料，請在左側點選「載入示範資料」或輸入 API Key 進行同步。")
    st.stop()


# 格式化時段名稱供選單呈現
def format_slot(slot):
    s, e = slot
    return f"{s[5:16]} ~ {e[5:16]}"

slot_options = [format_slot(slot) for slot in time_slots]


# 6. 分頁設計：地圖視覺化 / 趨勢圖表 / 資料庫清單
tab_map, tab_trend, tab_data = st.tabs([
    "🗺️ 台灣氣溫互動地圖 (Folium)", 
    "📈 各縣市氣溫趨勢分析 (Trend Charts)", 
    "📊 全台氣象資料檢視 (Data Table)"
])


# =========================================================================
# Tab 1: 台灣氣溫互動地圖 (Steps 17, 18, 19)
# =========================================================================
with tab_map:
    col_ctrl, col_metrics = st.columns([1, 3])

    with col_ctrl:
        st.subheader("⏱️ 選擇預報時段")
        selected_slot_idx = st.selectbox(
            "請選擇時段",
            options=range(len(slot_options)),
            format_func=lambda x: slot_options[x],
            index=0,
            label_visibility="collapsed"
        )
        selected_start_time = time_slots[selected_slot_idx][0]
        selected_end_time = time_slots[selected_slot_idx][1]

        st.info(f"📅 **當前預報區間**\n\n開始：`{selected_start_time}`\n\n結束：`{selected_end_time}`")

        st.markdown("""
        **🎨 溫度色階標示：**
        - <span style="color:#ef4444; font-weight:bold;">● 炎熱高溫 (> 30°C)</span>
        - <span style="color:#f59e0b; font-weight:bold;">● 溫暖宜人 (25°C ~ 30°C)</span>
        - <span style="color:#10b981; font-weight:bold;">● 舒適偏涼 (20°C ~ 25°C)</span>
        - <span style="color:#3b82f6; font-weight:bold;">● 偏冷低溫 (< 20°C)</span>
        """, unsafe_allow_html=True)

    # 取得當前時段的全台預報資料
    slot_df = get_forecasts_by_time(selected_start_time, "data.db")

    with col_metrics:
        if not slot_df.empty:
            max_row = slot_df.loc[slot_df['maxT'].idxmax()]
            min_row = slot_df.loc[slot_df['minT'].idxmin()]
            rain_row = slot_df.loc[slot_df['pop'].idxmax()]
            avg_temp = (slot_df['maxT'].mean() + slot_df['minT'].mean()) / 2

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔥 全台最高溫</div>
                    <div class="metric-value">{max_row['maxT']}°C</div>
                    <div class="metric-sub">{max_row['locationName']} ({max_row['weather']})</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">❄️ 全台最低溫</div>
                    <div class="metric-value">{min_row['minT']}°C</div>
                    <div class="metric-sub">{min_row['locationName']} ({min_row['weather']})</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🌧️ 最高降雨機率</div>
                    <div class="metric-value">{rain_row['pop']}%</div>
                    <div class="metric-sub">{rain_row['locationName']} ({rain_row['weather']})</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🌡️ 全台平均氣溫</div>
                    <div class="metric-value">{avg_temp:.1f}°C</div>
                    <div class="metric-sub">涵蓋 {len(slot_df)} 個縣市</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 繪製 Folium 台灣氣溫互動地圖 (Step 17 & 18)
    def get_temp_color(max_temp):
        if max_temp >= 30:
            return "#ef4444"  # 紅
        elif max_temp >= 25:
            return "#f59e0b"  # 橘
        elif max_temp >= 20:
            return "#10b981"  # 綠
        else:
            return "#3b82f6"  # 藍

    taiwan_map = folium.Map(
        location=[23.7, 120.9],
        zoom_start=7.4,
        tiles="CartoDB positron"
    )

    if not slot_df.empty:
        for _, row in slot_df.iterrows():
            loc_name = row['locationName']
            coords = (row['latitude'], row['longitude'])
            color = get_temp_color(row['maxT'])
            popup_html = f"""
            <div style="font-family: 'Noto Sans TC', sans-serif; min-width: 170px;">
                <h4 style="margin: 0 0 6px 0; color: #1e293b; border-bottom: 2px solid {color}; padding-bottom: 4px;">{loc_name}</h4>
                <p style="margin: 3px 0; font-size: 13px;"><b>天氣：</b>{row['weather']}</p>
                <p style="margin: 3px 0; font-size: 13px;"><b>溫度：</b>{row['minT']}°C ~ <span style="color: {color}; font-weight: bold;">{row['maxT']}°C</span></p>
                <p style="margin: 3px 0; font-size: 13px;"><b>降雨機率：</b>{row['pop']}%</p>
                <p style="margin: 3px 0; font-size: 13px;"><b>舒適度：</b>{row['ci']}</p>
            </div>
            """
            
            # 使用自訂 HTML 數字標籤圓點
            icon_html = f"""
            <div style="
                background-color: {color};
                color: white;
                font-weight: bold;
                border-radius: 50%;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                border: 2px solid white;
                font-size: 12px;
            ">
                {row['maxT']}°
            </div>
            """

            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{loc_name}：{row['weather']} ({row['minT']}°C ~ {row['maxT']}°C)",
                icon=folium.DivIcon(
                    icon_size=(32, 32),
                    icon_anchor=(16, 16),
                    html=icon_html
                )
            ).add_to(taiwan_map)

    st_folium(taiwan_map, width="100%", height=520)


# =========================================================================
# Tab 2: 各縣市氣溫趨勢分析 (Steps 13, 14, 15)
# =========================================================================
with tab_trend:
    st.subheader("📈 縣市 36 小時高低溫趨勢分析")
    
    col_sel, col_empty = st.columns([1, 2])
    with col_sel:
        selected_city = st.selectbox("請選擇欲查詢的縣市：", options=locations, index=locations.index("臺北市") if "臺北市" in locations else 0)

    city_df = get_forecasts_by_location(selected_city, "data.db")

    if not city_df.empty:
        # 縣市摘要資訊卡片
        c1, c2, c3, c4 = st.columns(4)
        latest_row = city_df.iloc[0]
        with c1:
            st.metric("即時預報天氣", f"{latest_row['weather']}")
        with c2:
            st.metric("預測最高溫", f"{city_df['maxT'].max()} °C", delta=f"{city_df['maxT'].max() - city_df['minT'].min()} °C 溫差")
        with c3:
            st.metric("預測最低溫", f"{city_df['minT'].min()} °C")
        with c4:
            st.metric("最高降雨機率", f"{city_df['pop'].max()} %")

        # 繪製 Plotly 高低溫互動走勢圖 (Step 14)
        time_labels = [f"{r['startTime'][5:16]}\n~{r['endTime'][11:16]}" for _, r in city_df.iterrows()]

        fig = go.Figure()

        # 最高溫曲線
        fig.add_trace(go.Scatter(
            x=time_labels,
            y=city_df['maxT'],
            mode='lines+markers+text',
            name='最高溫 (°C)',
            text=[f"{t}°C" for t in city_df['maxT']],
            textposition='top center',
            line=dict(color='#ef4444', width=3),
            marker=dict(size=10, color='#ef4444')
        ))

        # 最低溫曲線
        fig.add_trace(go.Scatter(
            x=time_labels,
            y=city_df['minT'],
            mode='lines+markers+text',
            name='最低溫 (°C)',
            text=[f"{t}°C" for t in city_df['minT']],
            textposition='bottom center',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=10, color='#3b82f6'),
            fill='tonexty',
            fillcolor='rgba(239, 68, 68, 0.08)'
        ))

        fig.update_layout(
            title=f"<b>{selected_city} 未來 36 小時氣溫走勢與預報</b>",
            xaxis_title="預報時段",
            yaxis_title="溫度 (°C)",
            yaxis=dict(range=[city_df['minT'].min() - 3, city_df['maxT'].max() + 3]),
            hovermode="x unified",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=60, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)

        # 顯示該縣市詳細資料表 (Step 15)
        st.markdown("##### 📋 詳細時段預報表")
        display_city_df = city_df[[
            'startTime', 'endTime', 'weather', 'minT', 'maxT', 'pop', 'ci'
        ]].rename(columns={
            'startTime': '開始時間',
            'endTime': '結束時間',
            'weather': '天氣現象',
            'minT': '最低溫 (°C)',
            'maxT': '最高溫 (°C)',
            'pop': '降雨機率 (%)',
            'ci': '舒適度指標'
        })
        st.dataframe(display_city_df, use_container_width=True, hide_index=True)


# =========================================================================
# Tab 3: 全台氣象資料檢視 (Steps 10, 12, 15)
# =========================================================================
with tab_data:
    st.subheader("📊 資料庫完整資料檢視 (SQLite - data.db)")
    all_df = get_all_forecasts("data.db")

    col_search, col_filter, col_dl = st.columns([2, 1, 1])
    with col_search:
        search_kw = st.text_input("🔍 搜尋縣市或天氣描述：", placeholder="輸入如：臺北、雷雨、晴天...")
    with col_filter:
        rain_filter = st.checkbox("僅看有降雨機率 (> 0%)", value=False)
    with col_dl:
        csv_data = all_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載完整 CSV 資料",
            data=csv_data,
            file_name="taiwan_weather_forecasts.csv",
            mime="text/csv",
            use_container_width=True
        )

    filtered_df = all_df.copy()
    if search_kw:
        filtered_df = filtered_df[
            filtered_df['locationName'].str.contains(search_kw, na=False) |
            filtered_df['weather'].str.contains(search_kw, na=False)
        ]
    if rain_filter:
        filtered_df = filtered_df[filtered_df['pop'] > 0]

    st.markdown(f"共篩選出 **{len(filtered_df)}** 筆紀錄：")
    st.dataframe(
        filtered_df[[
            'id', 'locationName', 'startTime', 'endTime', 'weather', 
            'minT', 'maxT', 'pop', 'ci', 'updatedAt'
        ]].rename(columns={
            'id': '序號',
            'locationName': '縣市名稱',
            'startTime': '預報起點',
            'endTime': '預報終點',
            'weather': '天氣狀況',
            'minT': '最低溫',
            'maxT': '最高溫',
            'pop': '降雨機率(%)',
            'ci': '體感舒適度',
            'updatedAt': '資料更新時間'
        }),
        use_container_width=True,
        hide_index=True
    )
