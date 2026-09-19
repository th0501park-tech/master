import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print("=" * 60)
    print("🚀 보성문화카렌다 웹 애플리케이션 서버를 시작합니다.")
    print(f"👉 접속 주소: http://{host}:{port}")
    print("=" * 60)
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)

