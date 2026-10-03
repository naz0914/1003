import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 讀取 .env
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

class Settings(BaseModel):
    # 中央氣象署 API 設定
    CWA_API_KEY: str = os.getenv("CWA_API_KEY", "CWA-8C2E2368-812D-4F61-8F55-8AFC60837532")
    CWA_DATA_URL: str = os.getenv("CWA_DATA_URL", "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001")
    CWA_AWS_DATA_URL: str = os.getenv("CWA_AWS_DATA_URL", "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001")
    
    # 快取存活時間 (秒) - 預設 10 分鐘
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "600"))

    # Windy Map Forecast API Key
    WINDY_API_KEY: str = os.getenv("WINDY_API_KEY", "")

    # CORS 允許來源
    ALLOWED_ORIGINS: list = ["*"]

settings = Settings()
