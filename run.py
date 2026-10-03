import uvicorn
import webbrowser
import threading
import time
import sys

def open_browser():
    time.sleep(1.5)
    print("🌐 正在為您自動開啟瀏覽器: http://localhost:8000 ...")
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=" * 65)
    print("🇹🇼 CWA × Windy 台灣即時氣溫視覺化系統 (FastAPI + Leaflet)")
    print("=" * 65)
    print("🚀 後端服務啟動中: http://localhost:8000")
    print("📖 Swagger API 互動文件: http://localhost:8000/docs")
    print("💡 按 Ctrl + C 可停止服務")
    print("=" * 65)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
