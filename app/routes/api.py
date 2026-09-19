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
