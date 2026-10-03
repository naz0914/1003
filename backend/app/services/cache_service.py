import time
import json
import logging
from pathlib import Path
from typing import Any, Optional, Tuple
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cache_snapshot.json"


class CacheService:
    """記憶體快取服務 (支援 TTL、冷啟動磁碟備援與狀態追蹤)"""

    def __init__(self):
        self._cache_data: Optional[Any] = None
        self._cached_at: float = 0.0
        self._ttl_seconds: int = 600
        self._latest_cwa_time: Optional[str] = None
        self._load_from_disk()

    def set(self, data: Any, ttl_seconds: int = 600, cwa_time: Optional[str] = None):
        self._cache_data = data
        self._cached_at = time.time()
        self._ttl_seconds = ttl_seconds
        if cwa_time:
            self._latest_cwa_time = cwa_time
        self._save_to_disk()

    def get(self) -> Tuple[Optional[Any], str]:
        """
        回傳 (資料, 快取狀態)
        狀態可能為 'none', 'fresh', 'stale'
        """
        if self._cache_data is None:
            return None, "none"

        now = time.time()
        if now - self._cached_at < self._ttl_seconds:
            return self._cache_data, "fresh"
        else:
            return self._cache_data, "stale"

    def is_fresh(self) -> bool:
        return (time.time() - self._cached_at) < self._ttl_seconds if self._cache_data else False

    def get_latest_cwa_time(self) -> Optional[str]:
        return self._latest_cwa_time

    def clear(self):
        self._cache_data = None
        self._cached_at = 0.0

    def _save_to_disk(self):
        """將快取落地儲存至磁碟，提供冷啟動備援 (Section 5 補強)"""
        try:
            SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            if hasattr(self._cache_data, "model_dump"):
                payload = {
                    "cached_at": self._cached_at,
                    "cwa_time": self._latest_cwa_time,
                    "data": self._cache_data.model_dump()
                }
                with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"儲存快取備援檔案失敗: {e}")

    def _load_from_disk(self):
        """伺服器冷啟動時從磁碟復原最後一次成功的觀測數據"""
        if not SNAPSHOT_PATH.exists():
            return
        try:
            from backend.app.schemas.temperature import LatestTemperatureResponse
            with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self._cached_at = payload.get("cached_at", 0)
            self._latest_cwa_time = payload.get("cwa_time")
            self._cache_data = LatestTemperatureResponse(**payload.get("data", {}))
            logger.info("成功自磁碟載入冷啟動快取備援資料")
        except Exception as e:
            logger.warning(f"讀取磁碟快取備援檔案失敗: {e}")


cache_service = CacheService()
