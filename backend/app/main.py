import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.routers.temperature import router as temperature_router
from backend.app.routers.health import router as health_router
from backend.app.jobs.refresh_cwa_data import cwa_refresh_worker
from backend.app.services.temperature_service import temperature_service

# 前端目錄路徑
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服務啟動時：預熱快取資料
    print("🚀 FastAPI 正在預熱 CWA 測站氣溫資料...")
    try:
        data = temperature_service.get_latest()
        print(f"✅ 預熱完成！已載入 {data.count} 個測站觀測紀錄。")
    except Exception as e:
        print(f"⚠️ 預熱快取警示: {e}")

    # 啟動背景定時排程更新工作
    refresh_task = asyncio.create_task(cwa_refresh_worker(settings.CACHE_TTL_SECONDS))
    yield
    # 服務關閉時：取消背景任務
    refresh_task.cancel()


app = FastAPI(
    title="CWA + Windy 台灣氣溫視覺化 API",
    description="結合中央氣象署 (CWA) 自動氣象站即時資料與 Windy Map Forecast API 的高精度氣象視覺化系統",
    version="1.0.0",
    lifespan=lifespan
)

# 設定 CORS 跨域資源共享 (Section 21)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 API 路由
app.include_router(temperature_router)
app.include_router(health_router)

# 掛載前端靜態檔案
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Frontend index.html not found, please check frontend directory."}
