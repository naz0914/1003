"""
Phase 2: 資料庫處理與存儲模組 (database.py)
負責 SQLite 資料庫結構設計 (data.db)、資料寫入 (INSERT / REPLACE) 與查詢操作 (SELECT)。
支援 Pandas DataFrame 與 SQLite 相互轉換。
"""

import sqlite3
import pandas as pd
from typing import List, Tuple, Dict, Any
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data.db"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """取得 SQLite 資料庫連線物件"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    """
    初始化 SQLite 資料庫與資料表結構 (Step 8 & 9)
    建立 TemperatureForecasts 資料表與唯一索引，確保資料不重複且可持續更新。
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        locationName TEXT NOT NULL,
        startTime TEXT NOT NULL,
        endTime TEXT NOT NULL,
        weather TEXT,
        pop INTEGER,
        minT INTEGER,
        maxT INTEGER,
        ci TEXT,
        latitude REAL,
        longitude REAL,
        updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(locationName, startTime, endTime)
    );
    """)

    # 建立常用查詢索引以加速視覺化篩選
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_forecast_loc_time 
    ON TemperatureForecasts (locationName, startTime);
    """)

    conn.commit()
    conn.close()
    logger.info(f"SQLite 資料庫初始化完成: {db_path}")


def save_forecasts(df: pd.DataFrame, db_path: str = DEFAULT_DB_PATH) -> int:
    """
    將 Pandas DataFrame 整理後的氣象資料寫入 SQLite (Step 9)
    使用 INSERT OR REPLACE 避免重複資料。
    """
    if df.empty:
        logger.warning("寫入資料庫時 DataFrame 為空")
        return 0

    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    insert_sql = """
    INSERT OR REPLACE INTO TemperatureForecasts (
        locationName, startTime, endTime, weather, pop, minT, maxT, ci, latitude, longitude, updatedAt
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
    """

    records = []
    for _, row in df.iterrows():
        records.append((
            row["locationName"],
            row["startTime"],
            row["endTime"],
            row.get("weather", ""),
            int(row.get("pop", 0)),
            int(row.get("minT", 0)),
            int(row.get("maxT", 0)),
            row.get("ci", ""),
            float(row.get("latitude", 23.7)),
            float(row.get("longitude", 120.9))
        ))

    cursor.executemany(insert_sql, records)
    conn.commit()
    count = len(records)
    conn.close()
    logger.info(f"成功存入 {count} 筆氣象預報資料至 {db_path}")
    return count


def get_all_forecasts(db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """從 SQLite 讀取所有預報紀錄為 Pandas DataFrame (Step 10 & 12)"""
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = get_connection(db_path)
    query = "SELECT * FROM TemperatureForecasts ORDER BY locationName, startTime ASC;"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_forecasts_by_location(location_name: str, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """查詢特定縣市的氣象預報資料 (Step 13)"""
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = get_connection(db_path)
    query = """
    SELECT * FROM TemperatureForecasts 
    WHERE locationName = ? 
    ORDER BY startTime ASC;
    """
    df = pd.read_sql_query(query, conn, params=(location_name,))
    conn.close()
    return df


def get_forecasts_by_time(start_time: str, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """查詢特定預報時段的全台縣市氣象資料 (供地圖渲染使用 Step 18)"""
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = get_connection(db_path)
    query = """
    SELECT * FROM TemperatureForecasts 
    WHERE startTime = ? 
    ORDER BY locationName ASC;
    """
    df = pd.read_sql_query(query, conn, params=(start_time,))
    conn.close()
    return df


def get_available_locations(db_path: str = DEFAULT_DB_PATH) -> List[str]:
    """取得資料庫中現有的所有縣市清單"""
    if not os.path.exists(db_path):
        return []

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT locationName FROM TemperatureForecasts ORDER BY locationName ASC;")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_available_time_slots(db_path: str = DEFAULT_DB_PATH) -> List[Tuple[str, str]]:
    """取得資料庫中現有的所有預報時段 (startTime, endTime)"""
    if not os.path.exists(db_path):
        return []

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT startTime, endTime FROM TemperatureForecasts ORDER BY startTime ASC;")
    rows = cursor.fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def get_db_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """取得資料庫摘要資訊 (總筆數、最後更新時間)"""
    if not os.path.exists(db_path):
        return {"total_records": 0, "last_updated": "無資料"}

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), MAX(updatedAt) FROM TemperatureForecasts;")
    row = cursor.fetchone()
    conn.close()

    return {
        "total_records": row[0] if row else 0,
        "last_updated": row[1] if row and row[1] else "無資料"
    }
