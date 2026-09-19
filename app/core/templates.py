import urllib.parse
from typing import Optional
from fastapi.templating import Jinja2Templates
from app.core.config import settings

templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

def safe_image(url: Optional[str]) -> str:
    """
    이미지 URL을 안전한 경로로 변환하는 Jinja2 커스텀 필터:
    1. 비어있는 경우 기본 no-image.svg 반환
    2. 로컬 정적 경로(/static/...)인 경우 그대로 반환
    3. HTTP URL 또는 인증서가 유효하지 않은 bosungcalendar.com URL은 /api/images/proxy 로 변환하여 HTTPS로 서빙
    """
    if not url:
        return "/static/images/no-image.svg"
    
    url_str = str(url).strip()
    if not url_str:
        return "/static/images/no-image.svg"
        
    if url_str.startswith("/") or url_str.startswith("./"):
        return url_str
        
    # HTTP URL이거나 bosungcalendar.com URL인 경우 프록시 처리 (Mixed Content 및 자체서명 SSL 방지)
    if url_str.startswith("http://") or "bosungcalendar.com" in url_str:
        encoded = urllib.parse.quote(url_str, safe="")
        return f"/api/images/proxy?url={encoded}"
        
    return url_str

# Jinja2 환경에 필터 및 글로벌 변수 등록
templates.env.filters["safe_image"] = safe_image
templates.env.globals["settings"] = settings

