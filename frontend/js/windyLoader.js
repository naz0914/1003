/**
 * 地圖引擎載入模組 (windyLoader.js)
 * 解決 CartoDB API Key 浮水印問題，改用 Esri / OpenStreetMap 免金鑰高畫質暗黑底圖
 */

let activeMap = null;
let activeStore = null;
let currentEngine = "leaflet"; // 'windy' 或 'leaflet'
let currentBaseLayer = null;
let currentRefLayer = null;

// 高品質免費底圖清單 (完全免金鑰、無任何浮水印)
const TILE_PRESETS = {
  esri_dark: {
    base: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    ref: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
    attribution: "&copy; Esri, HERE, Garmin &copy; CWA"
  },
  osm_streets: {
    base: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    ref: null,
    attribution: "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; CWA"
  },
  esri_imagery: {
    base: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    ref: "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attribution: "&copy; Esri, Maxar &copy; CWA"
  }
};

function switchBaseTile(presetKey = "esri_dark") {
  if (!activeMap) return;
  const preset = TILE_PRESETS[presetKey] || TILE_PRESETS.esri_dark;

  if (currentBaseLayer) activeMap.removeLayer(currentBaseLayer);
  if (currentRefLayer) activeMap.removeLayer(currentRefLayer);

  currentBaseLayer = L.tileLayer(preset.base, {
    attribution: preset.attribution,
    maxZoom: 18
  }).addTo(activeMap);

  if (preset.ref) {
    currentRefLayer = L.tileLayer(preset.ref, {
      maxZoom: 18,
      pane: "overlayPane"
    }).addTo(activeMap);
  }
}

async function initMapEngine(windyKey = "", onReady) {
  // 如果已有地圖實例，先清理
  if (activeMap) {
    activeMap.remove();
    activeMap = null;
    activeStore = null;
    currentBaseLayer = null;
    currentRefLayer = null;
  }

  // 1. 若有提供 Windy Key，嘗試初始化 Windy API
  if (windyKey && typeof window.windyInit === "function") {
    try {
      console.log("正在以提供的 Windy Key 初始化 Windy Map Forecast API...");
      const options = {
        key: windyKey,
        lat: 23.7,
        lon: 120.95,
        zoom: 7.5,
        overlay: "wind",
        verbose: false
      };

      window.windyInit(options, windyAPI => {
        const { map, store } = windyAPI;
        activeMap = map;
        activeStore = store;
        currentEngine = "windy";

        store.set("overlay", "wind");
        store.set("particlesAnim", "on");

        console.log("✅ Windy 地圖初始化成功！");
        if (onReady) onReady(map, store, "windy");
      });
      return;
    } catch (err) {
      console.warn("Windy 初始化失敗，自動切換至免金鑰高清 Leaflet 底圖:", err);
    }
  }

  // 2. 免金鑰標準 Leaflet 暗黑地圖模式 (使用無浮水印的 Esri World Dark Gray)
  console.log("啟動無浮水印之高清暗黑地圖 (Esri Dark Gray Base)...");
  activeMap = L.map("windy", {
    center: [23.7, 120.95],
    zoom: 7.6,
    minZoom: 6,
    maxZoom: 14,
    zoomControl: false
  });

  L.control.zoom({ position: "bottomright" }).addTo(activeMap);

  // 預設載入免金鑰深灰色高質感底圖
  switchBaseTile("esri_dark");

  currentEngine = "leaflet";
  if (onReady) onReady(activeMap, null, "leaflet");
}
