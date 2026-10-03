import asyncio
import logging
from backend.app.services.temperature_service import temperature_service

logger = logging.getLogger(__name__)

async def cwa_refresh_worker(interval_seconds: int = 600):
    """背景排程工作：定期從 CWA 更新氣象觀測資料 (Section 16: 每 10 分鐘)"""
    logger.info(f"啟動 CWA 自動刷新背景工作，間隔時間: {interval_seconds} 秒")
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            logger.info("背景排程：正在向 CWA 抓取最新測站氣溫...")
            data = temperature_service.get_latest(force_refresh=True)
            logger.info(f"背景排程完成：已更新 {data.count} 筆測站數據")
        except asyncio.CancelledError:
            logger.info("CWA 刷新背景工作已停止")
            break
        except Exception as e:
            logger.error(f"背景刷新 CWA 資料時發生錯誤: {e}")
