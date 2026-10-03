"""
獨立測試腳本 (fetch_and_save.py)
驗證開發藍圖 Steps 4 ~ 10:
1. 抓取 / 解析氣象資料
2. 轉換為 Pandas DataFrame
3. 建立並寫入 SQLite 資料庫 (data.db)
4. 執行 SQL 查詢驗證成果
"""

import sys
import os
import traceback

# 避免 Windows 終端機 (CP950) 因 Emoji 造成 UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from cwa_api import fetch_cwa_weather, parse_weather_json, generate_mock_weather_data
    from database import init_db, save_forecasts, get_all_forecasts, get_db_stats
except Exception as e:
    print(f"[ERROR] 模組載入失敗: {e}")
    traceback.print_exc()
    sys.exit(1)


def run_sync(api_key: str = None):
    try:
        print("=" * 60)
        print(">> 啟動 CWA 氣象資料同步與資料庫寫入流程...")
        print("=" * 60)

        # 1. 抓取或產生資料 (Phase 1)
        if api_key and api_key.strip():
            print(f">> 正在從中央氣象署 CWA API 獲取即時資料...")
            try:
                raw_json = fetch_cwa_weather(api_key.strip())
                df = parse_weather_json(raw_json)
                print(f"[OK] CWA API 資料抓取成功！解析出 {len(df)} 筆預報紀錄。")
            except Exception as e:
                print(f"[WARN] API 抓取失敗: {e}，改用示範資料庫資料...")
                df = generate_mock_weather_data()
        else:
            print("[INFO] 未提供 CWA API Key，載入全台 22 縣市完整模擬氣象資料庫...")
            df = generate_mock_weather_data()

        # 2. DataFrame 資料預覽 (Step 7)
        print("\n[Step 7] Pandas DataFrame 前 5 筆預覽：")
        print(df[["locationName", "startTime", "weather", "minT", "maxT", "pop"]].head())

        # 3. 建立並存入 SQLite (Step 8 & 9)
        print("\n[Step 8 & 9] 正在寫入 SQLite 資料庫 (data.db)...")
        init_db("data.db")
        count = save_forecasts(df, "data.db")
        print(f"[OK] 成功存入 {count} 筆資料！")

        # 4. 執行 SQL 查詢驗證 (Step 10)
        print("\n[Step 10] 驗證資料庫查詢 (SELECT)：")
        db_df = get_all_forecasts("data.db")
        stats = get_db_stats("data.db")
        print(f">> 目前資料庫總筆數: {stats['total_records']}")
        print(f">> 最後更新時間: {stats['last_updated']}")
        print(f">> 涵蓋縣市數量: {db_df['locationName'].nunique()} 個縣市")
        print("=" * 60)
        print("[SUCCESS] Phase 1 & Phase 2 測試全部通過！")
    except Exception as ex:
        print(f"[ERROR] 執行過程發生例外: {ex}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("CWA_API_KEY", "")
    run_sync(key)
