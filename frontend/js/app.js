/**
 * 前端主邏輯整合模組 (app.js)
 * 整合 Windy/Leaflet 地圖、CWA 測站圖層、篩選器、排行榜與語音播報
 */

let mapInstance = null;
let storeInstance = null;
let cwaLayerGroup = null;
let stationsData = [];
let countdownSeconds = 300; // 5 分鐘自動刷新
let countdownInterval = null;

// DOM 元素快取
const obsTimeEl = document.getElementById("cwa-obs-time");
const stationCountEl = document.getElementById("cwa-station-count");
const refreshBtn = document.getElementById("btn-refresh");
const refreshSpinner = document.getElementById("refresh-spinner");
const countdownEl = document.getElementById("countdown-timer");
const voiceBtn = document.getElementById("btn-voice-broadcast");

const selectCounty = document.getElementById("select-county");
const toggleMarkers = document.getElementById("toggle-markers");
const toggleLabels = document.getElementById("toggle-labels");
const toggleExcludeMountain = document.getElementById("toggle-exclude-mountain");

const btnEngineWindy = document.getElementById("btn-engine-windy");
const btnEngineLeaflet = document.getElementById("btn-engine-leaflet");
const windyLayersGroup = document.getElementById("windy-layers-group");
const leaderboardList = document.getElementById("leaderboard-list");
const leaderboardHeader = document.getElementById("leaderboard-header");
const leaderboardPanel = document.getElementById("leaderboard-panel");


// 1. 初始化入口
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  startCountdown();

  // 預設啟動地圖 (預設免金鑰 Leaflet 模式，若有設定 Windy 金鑰可切換)
  initMapEngine("", onMapReady);
});


// 地圖就緒回呼函式
function onMapReady(map, store, engine) {
  mapInstance = map;
  storeInstance = store;

  if (cwaLayerGroup) {
    cwaLayerGroup.clearLayers();
  }
  cwaLayerGroup = L.layerGroup().addTo(mapInstance);

  // 切換 UI 控制狀態
  if (engine === "windy") {
    btnEngineWindy.classList.add("active");
    btnEngineLeaflet.classList.remove("active");
    windyLayersGroup.style.display = "block";
  } else {
    btnEngineLeaflet.classList.add("active");
    btnEngineWindy.classList.remove("active");
    windyLayersGroup.style.display = "none";
  }

  // 載入氣象資料
  loadCwaData();
  loadLeaderboard();
}


// 2. 獲取並渲染 CWA 測站氣象數據
async function loadCwaData() {
  setLoading(true);
  try {
    const filters = {
      county: selectCounty.value,
      max_altitude: toggleExcludeMountain.checked ? 1000 : null
    };

    const data = await fetchLatestTemperature(filters);
    stationsData = data.stations || [];

    // 更新頂部資訊
    if (stationsData.length > 0) {
      obsTimeEl.textContent = stationsData[0].observed_at.replace("T", " ").substring(0, 16);
      stationCountEl.textContent = `${stationsData.length} 站`;
    }

    renderCwaMarkers();
  } catch (err) {
    console.error("載入 CWA 資料失敗:", err);
    obsTimeEl.textContent = "資料載入異常";
  } finally {
    setLoading(false);
  }
}


// 3. 渲染測站標記與氣溫徽章
function renderCwaMarkers() {
  if (!mapInstance || !cwaLayerGroup) return;
  cwaLayerGroup.clearLayers();

  if (!toggleMarkers.checked) return;

  const showLabels = toggleLabels.checked;

  stationsData.forEach(st => {
    const color = colorByTemperature(st.temperature_c);
    const radius = Math.max(12, Math.min(22, 10 + (st.temperature_c - 15) * 0.4));

    // 自訂高質感溫度數值徽章
    const iconHtml = `
      <div class="cwa-marker-badge" style="
        background-color: ${color};
        width: ${showLabels ? '34px' : '16px'};
        height: ${showLabels ? '34px' : '16px'};
      ">
        ${showLabels ? `${Math.round(st.temperature_c)}°` : ''}
      </div>
    `;

    const marker = L.marker([st.lat, st.lon], {
      icon: L.divIcon({
        className: "custom-div-icon",
        html: iconHtml,
        iconSize: [showLabels ? 34 : 16, showLabels ? 34 : 16],
        iconAnchor: [showLabels ? 17 : 8, showLabels ? 17 : 8]
      })
    });

    // 關鍵補強：阻斷事件冒泡 (stopPropagation)，防止觸發 Windy 原生地圖點擊
    marker.on("click", (e) => {
      L.DomEvent.stopPropagation(e);
    });

    // 紫外線等級樣式
    let uvClass = "uv-low";
    if (st.uv_index >= 8) uvClass = "uv-danger";
    else if (st.uv_index >= 6) uvClass = "uv-high";
    else if (st.uv_index >= 3) uvClass = "uv-mid";

    // 彈出視窗 Popup
    const popupHtml = `
      <div class="cwa-popup-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h4 style="margin:0; color:#38bdf8;">${st.station_name}</h4>
          <span style="background:${color}; color:white; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:bold;">
            ${st.temperature_c.toFixed(1)}°C
          </span>
        </div>
        <div style="color:#94a3b8; font-size:12px; margin-top:2px;">
          ${st.county || ''} ${st.town || ''} (測站: ${st.station_id})
        </div>
        <div class="popup-grid">
          <div>天氣：<b>${st.weather || '多雲'}</b></div>
          <div>濕度：<b>${st.humidity_percent !== null ? st.humidity_percent + '%' : '-'}</b></div>
          <div>風速：<b>${st.wind_speed_mps !== null ? st.wind_speed_mps + ' m/s' : '-'}</b></div>
          <div>氣壓：<b>${st.pressure_hpa !== null ? st.pressure_hpa + ' hPa' : '-'}</b></div>
          <div>雨量：<b>${st.precipitation_mm !== null ? st.precipitation_mm + ' mm' : '0.0 mm'}</b></div>
          <div>海拔：<b>${st.altitude_m !== null ? Math.round(st.altitude_m) + ' m' : '-'}</b></div>
        </div>

        <!-- 生活氣象與穿搭小物指南 -->
        <div class="lifestyle-section">
          <div class="lifestyle-header">
            <span class="lifestyle-title">☀️ 紫外線與舒適度</span>
            <span class="uv-badge ${uvClass}">${st.uv_level || '中量級'}</span>
          </div>
          <div style="font-size:11px; color:#cbd5e1;">💧 ${st.comfort_text || '體感舒適'}</div>

          <div style="font-size:11px; font-weight:700; color:#facc15; margin-top:2px;">👕 建議穿著：</div>
          <div class="dressing-box">${st.dressing_advice || '舒適透氣衣物'}</div>

          <div class="essentials-title">🎒 出門必帶推薦小物：</div>
          <div class="essentials-tags">
            ${(st.essentials || ['☔ 晴雨傘', '🧴 防曬乳', '💧 隨身水瓶']).map(item => `<span class="essential-tag">${item}</span>`).join('')}
          </div>
        </div>

        <div style="font-size:11px; color:#64748b; margin-top:8px; border-top:1px solid rgba(255,255,255,0.1); padding-top:4px;">
          觀測時間：${st.observed_at.replace("T", " ")}
        </div>
      </div>
    `;

    marker.bindPopup(popupHtml, { maxWidth: 320, minWidth: 260 });
    marker.addTo(cwaLayerGroup);
  });
}


// 4. 載入前 10 大最熱測站排行榜
async function loadLeaderboard() {
  try {
    const topList = await fetchTopHottest(10);
    leaderboardList.innerHTML = "";

    topList.forEach((st, idx) => {
      const item = document.createElement("div");
      item.className = "ranking-item";
      item.innerHTML = `
        <div>
          <span class="ranking-badge">#${idx + 1}</span>
          <span style="font-weight:600;">${st.station_name}</span>
          <span style="color:#94a3b8; font-size:11px;">(${st.county || ''})</span>
        </div>
        <span class="ranking-temp">${st.temperature_c.toFixed(1)}°C</span>
      `;

      // 點擊排行榜項目直接飛至該測站
      item.addEventListener("click", () => {
        if (mapInstance) {
          mapInstance.flyTo([st.lat, st.lon], 11, { duration: 1.2 });
        }
      });

      leaderboardList.appendChild(item);
    });
  } catch (err) {
    leaderboardList.innerHTML = `<div style="color:#94a3b8; font-size:12px;">暫無排行資料</div>`;
  }
}


// 5. 語音播報功能 (Web Speech API)
function playVoiceBroadcast() {
  if (!("speechSynthesis" in window)) {
    alert("您的瀏覽器不支援語音合成播報功能");
    return;
  }

  if (stationsData.length === 0) {
    alert("目前尚無測站資料可供播報");
    return;
  }

  const sorted = [...stationsData].sort((a, b) => b.temperature_c - a.temperature_c);
  const hottest = sorted[0];
  const coldest = sorted[sorted.length - 1];
  const avg = (stationsData.reduce((acc, s) => acc + s.temperature_c, 0) / stationsData.length).toFixed(1);

  const uviInfo = hottest.uv_level ? `今日紫外線強度為${hottest.uv_level}。` : '';
  const dressingInfo = hottest.dressing_advice ? `穿搭建議：${hottest.dressing_advice}。` : '';
  const text = `中央氣象署即時天氣與生活穿搭播報。目前全台最高溫出現在 ${hottest.county || ''}${hottest.station_name}，氣溫高達 ${hottest.temperature_c.toFixed(1)} 度，天氣為 ${hottest.weather || '晴朗'}。全台最低溫出現在 ${coldest.station_name}，為 ${coldest.temperature_c.toFixed(1)} 度。全台平均氣溫約為 ${avg} 度。${uviInfo}${dressingInfo}提醒您外出請攜帶防曬用品與隨身水瓶，午後有降雨機率，建議隨身攜帶雨具！`;

  window.speechSynthesis.cancel(); // 停止先前的播報
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "zh-TW";
  utterance.rate = 1.05;
  window.speechSynthesis.speak(utterance);
}


// 6. 事件監聽配置
function setupEventListeners() {
  // 刷新按鈕
  refreshBtn.addEventListener("click", async () => {
    countdownSeconds = 300;
    await refreshCwaData();
    await loadCwaData();
    await loadLeaderboard();
  });

  // 語音播報按鈕
  voiceBtn.addEventListener("click", playVoiceBroadcast);

  // 篩選器事件
  selectCounty.addEventListener("change", loadCwaData);
  toggleExcludeMountain.addEventListener("change", loadCwaData);
  toggleMarkers.addEventListener("change", renderCwaMarkers);
  toggleLabels.addEventListener("change", renderCwaMarkers);

  // 底圖引擎切換
  btnEngineWindy.addEventListener("click", () => {
    const key = prompt("請輸入您的 Windy Map Forecast API Key:", "");
    if (key !== null) {
      initMapEngine(key.trim(), onMapReady);
    }
  });

  btnEngineLeaflet.addEventListener("click", () => {
    initMapEngine("", onMapReady);
  });

  // 底圖風格切換 (Esri Dark / OSM / Satellite)
  const selectBasemap = document.getElementById("select-basemap");
  if (selectBasemap) {
    selectBasemap.addEventListener("change", (e) => {
      if (typeof switchBaseTile === "function") {
        switchBaseTile(e.target.value);
      }
    });
  }

  // Windy 圖層切換
  document.querySelectorAll(".layer-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".layer-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const overlay = btn.getAttribute("data-overlay");
      if (storeInstance) {
        storeInstance.set("overlay", overlay);
      }
    });
  });

  // 排行榜抽屜折疊
  leaderboardHeader.addEventListener("click", () => {
    leaderboardPanel.classList.toggle("collapsed");
    const arrow = leaderboardHeader.querySelector(".toggle-arrow");
    arrow.textContent = leaderboardPanel.classList.contains("collapsed") ? "▼" : "▲";
    leaderboardList.style.display = leaderboardPanel.classList.contains("collapsed") ? "none" : "flex";
  });
}


// 7. 倒數計時器
function startCountdown() {
  if (countdownInterval) clearInterval(countdownInterval);
  countdownInterval = setInterval(() => {
    countdownSeconds--;
    if (countdownSeconds <= 0) {
      countdownSeconds = 300;
      loadCwaData();
      loadLeaderboard();
    }
    const mins = Math.floor(countdownSeconds / 60);
    const secs = countdownSeconds % 60;
    countdownEl.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }, 1000);
}

function setLoading(isLoading) {
  if (isLoading) {
    refreshSpinner.style.animation = "spin 1s linear infinite";
  } else {
    refreshSpinner.style.animation = "none";
  }
}
