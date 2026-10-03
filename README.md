# 🇹🇼 Taiwan Weather Forecast & CWA × Windy 台灣即時氣溫視覺化平台

[![Live Demo](https://img.shields.io/badge/Live%20Website-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://irbwsbs7a8fkzta3ztaxxd.streamlit.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-naz0914%2F1003-blue?logo=github)](https://github.com/naz0914/1003)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-green?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![CWA Open Data](https://img.shields.io/badge/CWA-Open%20Data-orange)](https://opendata.cwa.gov.tw/)

> 本專案結合**中央氣象署 (CWA) 開放資料**、**SQLite 結構化存儲**、**Windy Map Forecast API** 與 **Leaflet 高解析度地圖**，打造具備即時資料串接、7 階氣溫色階、Top 10 排行榜、高山海拔篩選與瀏覽器語音播報的現代化全方位氣象平台。

---

## 📸 實機畫面展示 (Live Preview)

<div align="center">
  <img src="screenshot.png" alt="Taiwan Weather Dashboard 實機運行截圖" width="100%" />
  <p><em>▲ CWA × Windy 台灣即時氣溫播報系統：測站氣溫色階標記、紫外線等級、建議穿著與出門必備小物指南</em></p>
</div>

---

## 🌐 網站與專案相關連結 (Important Links)

| 項目名稱 | 連結網址 | 說明 |
| :--- | :--- | :--- |
| 🚀 **線上正式公開網站 (Live Website)** | [https://irbwsbs7a8fkzta3ztaxxd.streamlit.app/](https://irbwsbs7a8fkzta3ztaxxd.streamlit.app/) | 🔥 **免安裝、免開終端機，手機與電腦點開即看！** |
| 📦 **GitHub 專案倉庫** | [https://github.com/naz0914/1003](https://github.com/naz0914/1003) | 完整開源原始碼與版本控制紀錄 |
| 🗺️ **CWA × Windy 即時地圖 (本地)** | [http://localhost:8000](http://localhost:8000) | 現代化暗黑地圖、氣象測站標籤、語音播報 |
| 📖 **FastAPI Swagger API 文件** | [http://localhost:8000/docs](http://localhost:8000/docs) | 互動式 RESTful API 文件與在線測試 |
| 📊 **Streamlit 氣象預報儀表板 (本地)** | [http://localhost:8501](http://localhost:8501) | 36小時高低溫走勢、Folium 地圖、歷史查詢 |
| 📡 **中央氣象署 CWA 開放資料平台** | [https://opendata.cwa.gov.tw/](https://opendata.cwa.gov.tw/) | 氣象資料來源與 API Key 申請入口 |
| 💨 **Windy 開發者平台 (Map Forecast API)** | [https://api.windy.com/](https://api.windy.com/) | 國際級動態風場與氣象底圖 API 文件 |

---

## 🌟 專案核心優勢與亮點特色 (Core Strengths & Highlights)

本專案跳脫傳統氣象儀表板的生硬表格，從**使用者體驗、資料管線工程**到**現代前端視覺設計**進行全面升級：

### 💎 六大核心競爭優勢

1. 🎨 **極致現代美學 (Glassmorphism & Dark Mode)**  
   採用暗黑科技風與磨砂玻璃擬態（Backdrop Blur）視覺設計，搭配細緻的微互動動畫與流暢陰影，擺脫傳統政府氣象網頁的呆板感。
2. 🧠 **AI 生活管家：穿搭指南與出門小物推薦**  
   不單只是冷冰冰的數字！系統自動綜合**氣溫、紫外線強度 (UV) 與相對濕度**，即時演算給出**「今日建議穿搭」**（如：透氣排汗、防風外套）與**「出門必備小物標籤」**（☔ 晴雨傘、🧴 防曬乳、💧 隨身補水瓶）。
3. 🎙️ **真人中文語音即時播報 (Web Speech API)**  
   內建無障礙與前衛感兼具的瀏覽器語音合成引擎，點擊一鍵即可聆聽全台最高溫測站、紫外線警示與外出叮嚀。
4. 🗺️ **零浮水印純淨高畫質圖資 (Zero-Watermark Maps)**  
   精準規避 CartoDB 等商業圖資的強制浮水印限制，選用 **OpenStreetMap 標準道路** 與 **Esri Dark Gray 科技暗灰** 高解析度底圖，視覺純淨專業。
5. ⚡ **全台 Top 10 最高溫排行榜與高山智慧過濾**  
   左下角即時計算全台前 10 熱門高溫測站，**點擊即可平滑飛行 (flyTo)** 聚焦該站；同時提供「排除高山測站 (>1000m)」切換開關，避免合歡山、玉山等高海拔低溫扭曲生活平地氣溫評估。
6. 🚀 **雙引擎彈性架構 (Dual-Engine Architecture)**  
   - **雲端免部署版 (Streamlit Cloud)**：手機、平板、電腦打開網址直接用，免終端機、免安裝環境。
   - **專業工程版 (FastAPI + SQLite + Leaflet)**：具備 5 分鐘快取機制、非同步 API、自動定時排程與完整 Swagger 互動文件。

---

### 📋 完整功能矩陣清單 (Feature Matrix)

| 功能模組 | 功能項目 | 具體描述與亮點 |
| :--- | :--- | :--- |
| **即時地圖** | 🌡️ 7 階動態氣溫色階 | 根據溫度由低至高自動顯色（深藍 ➔ 藍 ➔ 綠 ➔ 黃 ➔ 橘 ➔ 紅 ➔ 深紅） |
| **即時地圖** | 📌 互動測站資訊卡 | 點擊標記即刻展開氣溫、天氣現象、風速、濕度、降雨量與海拔高度 |
| **生活指引** | ☀️ 紫外線等級評估 | 依據氣象即時數據分析 UV 強度（微量、中量、過量、危險級） |
| **生活指引** | 👕 智慧穿戴指南 | 根據體感舒適度自動生成最適穿著建議 |
| **生活指引** | 🎒 外出必備小物 | 標籤化提醒攜帶折疊傘、防曬用品或隨身水瓶 |
| **導航探索** | 🔥 Top 10 高溫排行榜 | 即時排序最高溫站點，點擊平滑巡航 (Smooth FlyTo) |
| **導航探索** | ⛰️ 排除高山測站 | 一鍵過濾海拔高於 1000 公尺測站，貼近生活圈實況 |
| **導航探索** | 🏙️ 22 縣市快速選單 | 快速聚焦各縣市（台北、台中、高雄、花東等）生活氣象 |
| **語音互動** | 🎙️ 中文氣象語音播報 | 整合瀏覽器原生 Web Speech API，語音播報目前天氣與外出叮嚀 |
| **趨勢分析** | 📈 36 小時預報走勢 | Plotly 互動式折線圖，呈現高低溫走勢、溫差帶與降雨機率 |
| **資料存儲** | 💾 SQLite 結構化資料庫 | 本地儲存 `data.db`，支援唯一限制防重複寫入、查詢與統計 |
| **後端服務** | ⚡ FastAPI RESTful API | 提供 `/api/v1/stations/latest` 與 GeoJSON 格式，支援 5 分鐘記憶體快取 |

---

## 📌 系統架構流程圖 (System Architecture)

### 模式一：24 步微課程標準資料管線流程圖 (Streamlit + SQLite)

```mermaid
graph TD
    A["中央氣象署 CWA Open Data API (F-C0032-001)"] -->|"HTTP Requests / JSON"| B["cwa_api.py (資料獲取與解析)"]
    B -->|"Pandas DataFrame 資料清洗"| C[("SQLite 資料庫 (data.db)")]
    C -->|"SQL 查詢 / 讀取"| D["app.py (Streamlit 儀表板應用)"]
    D --> E["🗺️ Folium 台灣氣溫互動地圖"]
    D --> F["📈 Plotly 高低溫走勢圖"]
    D --> G["📋 全台縣市詳細氣象數據表"]
```

---

### 模式二：CWA × Windy 現代化即時地圖與語音播報架構 (FastAPI + Leaflet)

```mermaid
graph TD
    CWA["中央氣象署 CWA API (O-A0001-001 / O-A0003-001)"] -->|"HTTP Fetch / 快取 TTL"| BE["FastAPI 後端服務 (localhost:8000)"]
    BE -->|"JSON 正規化 / GeoJSON"| FE["Glassmorphism 前端網頁"]
    FE --> W1["🗺️ Esri Dark / OSM 高畫質暗黑地圖"]
    FE --> W2["💨 Windy 動態風場粒子層"]
    FE --> W3["🎙️ 瀏覽器即時中文語音播報"]
    FE --> W4["🔥 Top 10 全台最高溫排行榜"]
```

---

## 🗺️ 24 步開發藍圖實現對照 (Curriculum Mapping)

| 階段 | 步驟 | 核心任務 | 對應實作檔案 / 模組 |
| :--- | :--- | :--- | :--- |
| **Phase 1: 資料獲取與解析** | Steps 1~6 | CWA API 串接、取得 JSON、提取縣市與 MinT/MaxT | `cwa_api.py` (`fetch_cwa_weather`, `parse_weather_json`) |
| **Phase 2: 資料處理與存儲** | Steps 7~10 | Pandas DataFrame 清洗、設計 SQLite Table、SQL 存取 | `database.py` (`init_db`, `save_forecasts`, `get_all_forecasts`) |
| **Phase 3: 儀表板介面開發** | Steps 11~16 | Streamlit 基礎建構、縣市選單、氣溫折線圖、版面整合 | `app.py` (Tab 2: 氣溫趨勢分析與時段預報表) |
| **Phase 4: 進階視覺化與優化** | Steps 17~20 | Folium 台灣地圖、溫度色階標記、時段切換器、效能快取 | `app.py` (Tab 1: 台灣氣象地圖與指標卡片) |
| **Phase 5: 版本控制與上線** | Steps 21~24 | Git 提交、推送 GitHub 倉庫、架構回顧與延伸應用 | Git Commit & Push / 專案文檔與教學說明 |

---

## 🚀 快速啟動指南 (Quick Start)

### 1. 安裝環境與套件

```powershell
# 建立並進入虛擬環境 (如已有 .venv 可略過)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安裝所有必要套件
pip install -r requirements.txt
```

---

### 2. 啟動模式一：【CWA × Windy 現代化即時地圖與語音播報版】

```powershell
.venv\Scripts\python.exe run.py
```
> 啟動後系統會**自動在瀏覽器開啟** [http://localhost:8000](http://localhost:8000)
> - 🌌 **免金鑰高畫質底圖**：採用 Esri Dark Gray 科技暗黑地圖（完全無浮水印）。
> - 🎙️ **即時語音播報**：點擊「語音播報」按鈕，聆聽全台即時氣候概況。
> - 🔥 **Top 10 排行榜**：點擊排行榜測站，地圖平滑飛行 (flyTo) 到該測站並展開卡片。
> - ⛰️ **高山篩選**：勾選「排除高山測站 (>1000m)」，專注生活平地氣溫。

---

### 3. 啟動模式二：【Streamlit 台灣氣象預報儀表板版】

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```
> 啟動後自動開啟 [http://localhost:8501](http://localhost:8501)
> - 包含全台 22 縣市 36 小時預報時段切換、高低溫雙曲線走勢圖與 SQLite 資料庫歷史查詢。

---

## ☁️ 如何將網站免費部署至雲端 (Deploy Online)

若想讓其他人也可以透過手機或公開網址瀏覽您的成品，推薦以下免費部署方式：

### 方式 A：部署 Streamlit 版至 Streamlit Community Cloud (最簡單)
1. 前往 [Streamlit Community Cloud](https://share.streamlit.io/) 並使用 GitHub 帳號登入。
2. 點選 **"New app"**。
3. Repository 選擇 `naz0914/1003`，Main file path 輸入 `app.py`。
4. 點選 **"Deploy!"**，幾分鐘後即可取得專屬公開網址（例如：`https://1003-weather.streamlit.app`）。

### 方式 B：部署 FastAPI 版至 Render 或 Railway
1. 前往 [Render.com](https://render.com/)，點選 **New Web Service** 連接 GitHub 倉庫 `naz0914/1003`。
2. Build Command 設定：`pip install -r requirements.txt`
3. Start Command 設定：`uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. 部署完成即可獲得公開 HTTPS 網址！

---

## 🔑 中央氣象署 (CWA) API 授權碼設定

本專案已在 `.env` 中為您配置授權碼：
```env
CWA_API_KEY=CWA-8C2E2368-812D-4F61-8F55-8AFC60837532
```
若需更換，可至 [中央氣象署開放資料平台](https://opendata.cwa.gov.tw/) 登入會員並在「取得授權碼」重新生成。

---

## 📂 專案檔案結構清單

```text
hw3/
├── run.py                       # 🚀 模式一啟動入口 (FastAPI + 自動開啟瀏覽器)
├── app.py                       # 📊 模式二啟動入口 (Streamlit 網頁儀表板)
├── design.md                    # 📑 5 大補強架構設計規格書
├── README.md                    # 📖 專案綜合說明文件與連結導航
├── requirements.txt             # 專案相依套件清單
├── data.db                      # SQLite 本地氣象資料庫
├── .env                         # 本地環境變數設定
│
├── backend/                     # FastAPI 後端模組
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py              # FastAPI 核心應用與靜態檔案路由
│       ├── config.py            # 設定載入
│       ├── schemas/             # Pydantic 資料模型 (Station, GeoJSON, Health)
│       ├── services/            # CWA 資料抓取、清洗與快取
│       ├── routers/             # API 路由 (/latest, /geojson, /health)
│       └── jobs/                # 背景定時刷新排程
│
└── frontend/                    # 現代化純前端 UI 介面
    ├── index.html               # 玻璃擬態主頁面
    ├── css/style.css            # 暗黑科技感樣式表
    └── js/                      # 模組化 JS (地圖載入器、色碼表、API客戶端)
```
