from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import queries

router = APIRouter(prefix="/api")

class QuoteCreateRequest(BaseModel):
    author_name: str
    phone: str
    title: str
    content: str
    product_id: Optional[int] = None
    inquiry_type: str = "견적문의"
    email: Optional[str] = None
    quantity: Optional[int] = None
    password: Optional[str] = None

@router.get("/categories")
def list_categories():
    """카테고리 목록 API"""
    return queries.get_categories()

@router.get("/products/{product_id}")
def get_product(product_id: int):
    """상품 상세 API"""
    prod = queries.get_product_by_id(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

@router.post("/quotes")
def submit_quote(data: QuoteCreateRequest):
    """견적 문의 등록 API"""
    quote_id = queries.create_quote(
        author_name=data.author_name,
        phone=data.phone,
        title=data.title,
        content=data.content,
        product_id=data.product_id,
        inquiry_type=data.inquiry_type,
        email=data.email,
        quantity=data.quantity,
        password=data.password
    )
    return {"success": True, "quote_id": quote_id, "message": "견적 문의가 정상 접수되었습니다."}


# SSL 검증 우회 컨텍스트 (self-signed 인증서 사이트 호환)
import ssl
import urllib.request
from fastapi import Response, Query

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

@router.get("/images/proxy")
def proxy_image(url: str = Query(..., description="원본 이미지 URL")):
    """외부 HTTP/HTTPS 이미지를 안전하게 HTTPS로 중계 및 캐싱 서빙"""
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="올바르지 않은 이미지 URL입니다.")

    try:
        req = urllib.request.Request(url, headers=PROXY_HEADERS)
        with urllib.request.urlopen(req, timeout=8, context=_ssl_ctx) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            image_data = resp.read()
            return Response(
                content=image_data,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=604800, immutable",
                }
            )
    except Exception as e:
        # 실패 시 404
        raise HTTPException(status_code=404, detail=f"이미지를 불러올 수 없습니다: {str(e)}")

