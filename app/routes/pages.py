from typing import Optional
from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.db import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

def common_context(request: Request, extra: dict = None) -> dict:
    """모든 템플릿에 공통으로 전달되는 컨텍스트 (카테고리 목록, 회사 정보 등)"""
    admin_id = request.session.get("admin_id") if hasattr(request, "session") else None
    admin_name = request.session.get("admin_name") if hasattr(request, "session") else None
    ctx = {
        "categories": queries.get_categories(),
        "settings": settings,
        "is_admin": bool(admin_id),
        "admin_name": admin_name,
    }
    if extra:
        ctx.update(extra)
    return ctx

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """메인 홈 화면"""
    featured_products = queries.get_featured_products(limit=8)
    notices = queries.get_posts(board_type="notice", limit=5)
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=common_context(request, {
            "featured_products": featured_products,
            "notices": notices,
            "title": f"{settings.COMPANY_NAME} - 공식 쇼핑몰"
        })
    )

@router.get("/category/{slug}", response_class=HTMLResponse)
async def category_page(
    request: Request,
    slug: str,
    page: int = Query(1, ge=1),
    search: Optional[str] = None,
    sort: str = "newest"
):
    """카테고리별 상품 목록 화면"""
    category = queries.get_category_by_slug(slug)
    if not category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

    products, total = queries.get_products_by_category(
        category_id=category["id"],
        search=search,
        sort=sort,
        page=page,
        per_page=12
    )

    total_pages = (total + 11) // 12

    return templates.TemplateResponse(
        request=request,
        name="products/list.html",
        context=common_context(request, {
            "category": category,
            "products": products,
            "total": total,
            "current_page": page,
            "total_pages": total_pages,
            "search": search or "",
            "sort": sort,
            "title": f"{category['name']} - {settings.COMPANY_NAME}"
        })
    )

@router.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail_page(request: Request, product_id: int):
    """상품 상세 페이지 (월별 내지 이미지 뷰어 포함)"""
    product = queries.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    return templates.TemplateResponse(
        request=request,
        name="products/detail.html",
        context=common_context(request, {
            "product": product,
            "title": f"{product['name']} ({product['item_code']}) - {settings.COMPANY_NAME}"
        })
    )

@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = Query("", min_length=1)):
    """상품 검색 결과 화면"""
    products = queries.search_products(q, limit=30)
    return templates.TemplateResponse(
        request=request,
        name="products/search.html",
        context=common_context(request, {
            "query": q,
            "products": products,
            "total": len(products),
            "title": f"'{q}' 검색 결과 - {settings.COMPANY_NAME}"
        })
    )

@router.get("/quotes", response_class=HTMLResponse)
async def quotes_list_page(request: Request, page: int = Query(1, ge=1)):
    """견적/구매 문의 게시판 목록"""
    per_page = 15
    offset = (page - 1) * per_page
    quotes = queries.get_quotes(limit=per_page, offset=offset)

    return templates.TemplateResponse(
        request=request,
        name="quotes/list.html",
        context=common_context(request, {
            "quotes": quotes,
            "current_page": page,
            "title": f"견적 및 주문 문의 - {settings.COMPANY_NAME}"
        })
    )

@router.get("/quotes/new", response_class=HTMLResponse)
async def quote_form_page(request: Request, product_id: Optional[int] = None):
    """견적/주문 문의 작성 폼 (상품 선택 연동)"""
    product = None
    if product_id:
        product = queries.get_product_by_id(product_id)

    return templates.TemplateResponse(
        request=request,
        name="quotes/form.html",
        context=common_context(request, {
            "product": product,
            "title": f"견적/주문 문의 작성 - {settings.COMPANY_NAME}"
        })
    )

@router.post("/quotes/new")
async def handle_quote_submit(
    request: Request,
    author_name: str = Form(...),
    phone: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    product_id: Optional[int] = Form(None),
    inquiry_type: str = Form("견적문의"),
    email: Optional[str] = Form(None),
    quantity: Optional[int] = Form(None),
    password: Optional[str] = Form(None)
):
    """견적 문의 폼 제출 처리"""
    quote_id = queries.create_quote(
        author_name=author_name,
        phone=phone,
        title=title,
        content=content,
        product_id=product_id,
        inquiry_type=inquiry_type,
        email=email,
        quantity=quantity,
        password=password
    )
    return RedirectResponse(url=f"/quotes?success=1", status_code=303)

@router.get("/company", response_class=HTMLResponse)
async def company_page(request: Request):
    """회사 소개 및 오시는 길"""
    return templates.TemplateResponse(
        request=request,
        name="company.html",
        context=common_context(request, {
            "title": f"회사소개 - {settings.COMPANY_NAME}"
        })
    )

# ==================== 공지사항 (Notice) 라우트 ====================
@router.get("/board/notice", response_class=HTMLResponse)
async def notice_list_page(request: Request, page: int = Query(1, ge=1)):
    """공지사항 목록 화면"""
    posts, total = queries.get_notices_paginated(page=page, per_page=10)
    total_pages = (total + 9) // 10

    return templates.TemplateResponse(
        request=request,
        name="boards/notice_list.html",
        context=common_context(request, {
            "posts": posts,
            "total": total,
            "current_page": page,
            "total_pages": total_pages,
            "title": f"공지사항 - {settings.COMPANY_NAME}"
        })
    )

@router.get("/board/notice/{post_id}", response_class=HTMLResponse)
async def notice_detail_page(request: Request, post_id: int):
    """공지사항 상세 화면"""
    post = queries.get_notice_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="해당 공지사항을 찾을 수 없습니다.")

    return templates.TemplateResponse(
        request=request,
        name="boards/notice_detail.html",
        context=common_context(request, {
            "post": post,
            "title": f"{post['title']} - 공지사항"
        })
    )

# ==================== 자주 묻는 질문 (FAQ) 라우트 ====================
@router.get("/board/faq", response_class=HTMLResponse)
async def faq_page(request: Request, category: str = Query("전체")):
    """FAQ 목록 화면 (아코디언 및 카테고리 필터)"""
    faqs = queries.get_faqs(category=category)
    faq_categories = ["전체"] + queries.get_faq_categories()

    return templates.TemplateResponse(
        request=request,
        name="boards/faq.html",
        context=common_context(request, {
            "faqs": faqs,
            "faq_categories": faq_categories,
            "selected_category": category,
            "title": f"자주 묻는 질문(FAQ) - {settings.COMPANY_NAME}"
        })
    )

# ==================== 질문과 답변 (Q&A) 라우트 ====================
@router.get("/board/qna", response_class=HTMLResponse)
async def qna_list_page(
    request: Request, 
    category: str = Query("전체"), 
    search: Optional[str] = None,
    page: int = Query(1, ge=1)
):
    """Q&A 게시판 목록 화면"""
    posts, total = queries.get_qna_posts(category=category, search=search, page=page, per_page=10)
    total_pages = (total + 9) // 10

    return templates.TemplateResponse(
        request=request,
        name="boards/qna_list.html",
        context=common_context(request, {
            "posts": posts,
            "total": total,
            "current_page": page,
            "total_pages": total_pages,
            "selected_category": category,
            "search": search or "",
            "title": f"질문과 답변(Q&A) - {settings.COMPANY_NAME}"
        })
    )

@router.get("/board/qna/new", response_class=HTMLResponse)
async def qna_form_page(request: Request):
    """새 질문 작성 폼"""
    return templates.TemplateResponse(
        request=request,
        name="boards/qna_form.html",
        context=common_context(request, {
            "title": f"질문 작성하기 - {settings.COMPANY_NAME}"
        })
    )

@router.post("/board/qna/new")
async def handle_qna_submit(
    request: Request,
    category: str = Form("일반문의"),
    title: str = Form(...),
    content: str = Form(...),
    author: str = Form(...),
    password: str = Form(...),
    is_secret: Optional[str] = Form(None)
):
    """새 질문 등록 처리"""
    secret_flag = True if is_secret == "on" or is_secret == "true" else False
    queries.create_qna_post(
        category=category,
        title=title,
        content=content,
        author=author,
        password=password,
        is_secret=secret_flag
    )
    return RedirectResponse(url="/board/qna?success=1", status_code=303)

@router.get("/board/qna/{qna_id}", response_class=HTMLResponse)
async def qna_detail_page(request: Request, qna_id: int, pw: Optional[str] = None):
    """Q&A 질문 및 답변 상세 화면 (비밀글 검증 포함)"""
    post = queries.get_qna_by_id(qna_id)
    if not post:
        raise HTTPException(status_code=404, detail="해당 질문을 찾을 수 없습니다.")

    # 비밀글 여부 확인
    is_authorized = True
    if post["is_secret"]:
        if not pw or pw != post["password"]:
            is_authorized = False

    return templates.TemplateResponse(
        request=request,
        name="boards/qna_detail.html",
        context=common_context(request, {
            "post": post,
            "is_authorized": is_authorized,
            "error_msg": "비밀번호가 일치하지 않습니다." if pw and not is_authorized else None,
            "title": f"{post['title']} - 질문과 답변"
        })
    )

