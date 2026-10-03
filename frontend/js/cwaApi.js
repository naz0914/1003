/**
 * CWA 後端 API 串接模組 (cwaApi.js)
 * 負責向 FastAPI 獲取正規化氣溫、GeoJSON 與 Top 10 排行數據
 */

const API_BASE = window.location.origin;

async function fetchLatestTemperature(filters = {}) {
  const query = new URLSearchParams();
  if (filters.county && filters.county !== "全部") query.append("county", filters.county);
  if (filters.max_altitude !== undefined && filters.max_altitude !== null) query.append("max_altitude", filters.max_altitude);

  const url = `${API_BASE}/api/temperature/latest?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: 獲取氣溫資料失敗`);
  return await res.json();
}

async function fetchTopHottest(limit = 10) {
  const url = `${API_BASE}/api/temperature/top-hottest?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: 獲取排行榜失敗`);
  return await res.json();
}

async function refreshCwaData() {
  const url = `${API_BASE}/api/temperature/refresh`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) throw new Error(`HTTP ${res.status}: 刷新資料失敗`);
  return await res.json();
}

async function checkHealth() {
  const url = `${API_BASE}/api/health`;
  const res = await fetch(url);
  return await res.json();
}
