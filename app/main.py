from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.templates import templates
from app.db.connection import init_db_pool, close_db_pool
from app.db.queries import seed_sample_notices
from app.routes import pages_router, api_router, admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: DB 커넥션 풀 초기화 및 샘플 데이터 시딩
    init_db_pool()
    try:
        seed_sample_notices()
    except Exception as e:
        print(f"[Warning] Failed to seed notices: {e}")
    yield
    # Shutdown: DB 커넥션 풀 정리
    close_db_pool()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# Session Middleware for Admin Authentication (24 hours session)
app.add_middleware(
    SessionMiddleware, 
    secret_key="bosung-calendar-super-secret-key-session-2026",
    max_age=86400
)

# Static files mount
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Register Routers
app.include_router(pages_router)
app.include_router(api_router)
app.include_router(admin_router)

# 404 Handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>페이지를 찾을 수 없습니다</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50 flex items-center justify-center min-h-screen">
            <div class="text-center p-8 bg-white rounded-2xl border border-gray-200 shadow-sm max-w-md">
                <div class="text-6xl font-black text-blue-600 mb-2">404</div>
                <h1 class="text-lg font-bold text-gray-800 mb-2">페이지를 찾을 수 없습니다.</h1>
                <p class="text-xs text-gray-500 mb-6">요청하신 페이지가 존재하지 않거나 주소가 변경되었습니다.</p>
                <a href="/" class="px-5 py-2.5 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700">홈으로 이동</a>
            </div>
        </body>
        </html>
        """,
        status_code=404
    )
