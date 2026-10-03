/**
 * 氣溫色碼表模組 (colorScale.js)
 * 嚴格對照 Section 15 設計規範
 */

function colorByTemperature(temp) {
  if (temp < 10) return "#2b6cb0";   // 寒冷 (<10°C)
  if (temp < 15) return "#3182ce";   // 涼爽 (10-15°C)
  if (temp < 20) return "#38a169";   // 溫和 (15-20°C)
  if (temp < 25) return "#ecc94b";   // 舒適 (20-25°C)
  if (temp < 30) return "#ed8936";   // 溫暖 (25-30°C)
  if (temp < 35) return "#e53e3e";   // 炎熱 (30-35°C)
  return "#9b2c2c";                  // 酷熱 (>35°C)
}

function getTemperatureCategory(temp) {
  if (temp < 10) return "寒冷";
  if (temp < 15) return "涼爽";
  if (temp < 20) return "溫和";
  if (temp < 25) return "舒適";
  if (temp < 30) return "溫暖";
  if (temp < 35) return "炎熱";
  return "酷熱";
}
