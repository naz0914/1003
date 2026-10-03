# 結合 Windy API 的中央氣象署 (CWA) 氣溫播報視覺化系統設計文件

## 1. 系統目標與定位
本系統旨在將台灣**中央氣象署 (CWA) 自動氣象站 (AWS)** 的即時觀測氣溫，疊加於 **Windy Map Forecast API (基於 Leaflet 1.4.x)** 之上，打造具備國際級天氣底圖與在地高精確測站數據的即時氣溫視覺化平台。

- **Windy**：負責宏觀天氣環境背景層（全球風場粒子、雲圖、降雨、氣溫數值模型）。
- **Leaflet**：負責微觀 CWA 觀測數據渲染（CircleMarker 測站標記、Popup 氣象卡片、熱力圖與色階標籤）。
- **FastAPI**：負責後端資料抓取、數值正規化、無效值過濾、記憶體快取與 RESTful API 提供。

---

## 2. 系統架構圖 (Mermaid)

```mermaid
flowchart TD
    subgraph Data Sources
        A1[CWA 自動氣象站 API<br/>O-A0001-001 / O-A0003-001]
    end

    subgraph Backend - FastAPI (Port 8000)
        B1[CWA Client 抓取模組] -->|Raw JSON| B2[正規化與資料清洗<br/>過濾 -99, 範圍檢查]
        B2 --> B3[Cache Service<br/>記憶體快取 TTL 10m]
        B3 --> B4[FastAPI Routers]
        B4 -->|GET /api/temperature/latest| B5[最新氣溫 JSON]
        B4 -->|GET /api/temperature/geojson| B6[Leaflet GeoJSON]
        B4 -->|GET /api/health| B7[健康檢查端點]
        B4 -->|GET /api/temperature/top-hottest| B8[Top 10 高溫測站]
    end

    subgraph Frontend - Windy + Leaflet
        C1[Windy Map Forecast API<br/>Leaflet 1.4.x / libBoot.js] --> C2[Windy 地圖實例]
        C2 --> C3[Windy 背景圖層: wind / temp / rain / clouds]
        B5 -->|AJAX Fetch (5m 輪詢)| D1[CWA Overlay LayerGroup]
        D1 -->|CircleMarker + Popup| C2
        D2[氣溫色階圖例 Legend] --> C2
        D3[縣市篩選器 & 語音播報] --> C2
    end

    A1 --> B1
```

---

## 3. 資料規範與驗證規則 (Validation Rules)

### 3.1 無效值過濾
以下字串或數值將視為無效值，自動轉換為 `None` 或直接捨棄該測站：
```python
INVALID_VALUES = {"", "X", "NA", "null", None, "-99", "-999", "-998"}
```

### 3.2 氣溫有效範圍
- **合格範圍**：$-20^\circ\text{C} \le \text{Temperature} \le 50^\circ\text{C}$
- 若超出此範圍，捨棄該氣溫紀錄以防止儀器故障異常值干擾地圖標記。

---

## 4. 氣溫色碼表 (Color Scale)

| 溫度區間 | 代表色碼 | 狀態定義 |
| :--- | :--- | :--- |
| $< 10^\circ\text{C}$ | `#2b6cb0` (深藍) | 寒冷 (Cold) |
| $10 \sim 15^\circ\text{C}$ | `#3182ce` (淺藍) | 涼爽 (Cool) |
| $15 \sim 20^\circ\text{C}$ | `#38a169` (翠綠) | 溫和 (Mild) |
| $20 \sim 25^\circ\text{C}$ | `#ecc94b` (明黃) | 舒適 (Comfortable) |
| $25 \sim 30^\circ\text{C}$ | `#ed8936` (橙色) | 溫暖 (Warm) |
| $30 \sim 35^\circ\text{C}$ | `#e53e3e` (鮮紅) | 炎熱 (Hot) |
| $> 35^\circ\text{C}$ | `#9b2c2c` (深紅) | 酷熱 (Very Hot) |

---

## 5. API 規格定義

1. `GET /api/temperature/latest`
   - 回傳所有驗證通過的最新測站觀測列表。
2. `GET /api/temperature/geojson`
   - 回傳標準 `FeatureCollection` 格式，供 Leaflet GeoJSON 直接載入。
3. `GET /api/temperature/stations/{station_id}`
   - 回傳單一測站的詳細氣象數據（含氣壓、濕度、風向風速、降水量）。
4. `GET /api/temperature/top-hottest`
   - 回傳全台前 10 大最高溫測站排行。
5. `GET /api/health`
   - 伺服器健康狀態、快取存活時間、CWA 資料更新時戳。
