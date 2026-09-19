from typing import Optional, List
from urllib.parse import quote
from fastapi import APIRouter, Request, Form, Query, HTTPException, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from app.core.config import settings
from app.core.templates import templates
from app.db import queries
from app.services import excel_service

router = APIRouter(prefix="/admin")

def get_current_admin(request: Request) -> Optional[dict]:
    """세션에서 현재 로그인된 관리자 확인"""
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return None
    return queries.get_admin_by_id(admin_id)

def has_permission(admin: Optional[dict], required_perm: str) -> bool:
    """관리자 권한 보유 여부 확인"""
    if not admin or not admin.get("is_active", True):
        return False
    if admin.get("role") == "super_admin":
        return True
    perms = [p.strip() for p in (admin.get("permissions") or "").split(",") if p.strip()]
    return "all" in perms or required_perm in perms

def admin_context(request: Request, current_admin: dict, extra: dict = None) -> dict:
    """관리자 템플릿 전용 공통 컨텍스트"""
    ctx = {
        "current_admin": current_admin,
        "settings": settings,
        "categories": queries.get_categories(),
        "has_perm": lambda p: has_permission(current_admin, p),
        "can_manage_users": has_permission(current_admin, "users"),
        "can_manage_products": has_permission(current_admin, "products"),
        "can_manage_quotes": has_permission(current_admin, "quotes"),
        "can_manage_qna": has_permission(current_admin, "qna"),
        "can_manage_notices": has_permission(current_admin, "notices"),
    }
    if extra:
        ctx.update(extra)
    return ctx

# ==================== 인증 (Login / Logout) ====================
@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: Optional[str] = None):
    """관리자 로그인 페이지"""
    if request.session.get("admin_id"):
        return RedirectResponse(url="/admin", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin/login.html",
        context={"error": error, "settings": settings, "title": f"관리자 로그인 - {settings.COMPANY_NAME}"}
    )

@router.post("/login")
async def handle_admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """관리자 로그인 처리"""
    admin = queries.authenticate_admin(username, password)
    if not admin:
        return RedirectResponse(url="/admin/login?error=1", status_code=303)

    request.session["admin_id"] = admin["id"]
    request.session["admin_name"] = admin["name"]
    return RedirectResponse(url="/admin", status_code=303)

@router.get("/logout")
async def handle_admin_logout(request: Request):
    """로그아웃"""
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)

# ==================== 관리자 대시보드 ====================
@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """대시보드 메인 요약"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    stats = queries.get_dashboard_stats()
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context=admin_context(request, admin, {
            "stats": stats,
            "title": f"관리자 대시보드 - {settings.COMPANY_NAME}"
        })
    )

# ==================== 상품 관리 ====================
@router.get("/products", response_class=HTMLResponse)
async def admin_products_list(
    request: Request,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    sort_by: str = Query("id"),
    order: str = Query("asc")
):
    """상품 목록 및 가격 관리 (정렬, 필터, 검색 지원)"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    products = queries.get_all_products_admin(
        search=search,
        category_id=category_id,
        sort_by=sort_by,
        order=order
    )
    
    excel_error_msg = request.session.pop("excel_error_msg", None)
    excel_errors = request.session.pop("excel_errors", None)

    return templates.TemplateResponse(
        request=request,
        name="admin/products_list.html",
        context=admin_context(request, admin, {
            "products": products,
            "search": search or "",
            "selected_category_id": category_id,
            "sort_by": sort_by.lower(),
            "order": order.lower(),
            "excel_error_msg": excel_error_msg,
            "excel_errors": excel_errors,
            "title": f"상품 및 가격 관리 - {settings.COMPANY_NAME}"
        })
    )

# ==================== 엑셀 양식 다운로드 & 업로드 ====================
@router.get("/products/template")
async def admin_download_product_template(request: Request):
    """상품 일괄 등록 엑셀 양식 다운로드"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    categories = queries.get_categories()
    excel_data = excel_service.generate_product_template_excel(categories)
    filename = quote("보성문화카렌다_상품등록양식.xlsx")
    return Response(
        content=excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )

@router.get("/products/export")
async def admin_export_products_excel(
    request: Request,
    search: Optional[str] = None,
    category_id: Optional[int] = None
):
    """현재 등록된 상품 목록 엑셀 다운로드"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    products = queries.get_all_products_admin(search=search, category_id=category_id)
    categories = queries.get_categories()
    excel_data = excel_service.generate_products_export_excel(products, categories)
    filename = quote("보성문화카렌다_등록상품목록.xlsx")
    return Response(
        content=excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )

@router.post("/products/upload-excel")
async def admin_upload_products_excel(
    request: Request,
    file: UploadFile = File(...),
    update_existing: Optional[str] = Form("on")
):
    """엑셀 파일 업로드 상품 일괄 등록"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    file_bytes = await file.read()
    should_update = (update_existing in ["on", "true", "1", True])

    result = excel_service.parse_and_import_products(
        file_bytes=file_bytes,
        filename=file.filename,
        update_existing=should_update
    )

    if not result.get("success"):
        request.session["excel_error_msg"] = result.get("message", "엑셀 처리 중 오류가 발생했습니다.")
        return RedirectResponse(url="/admin/products?excel_error=1", status_code=303)

    if result.get("errors"):
        request.session["excel_errors"] = result["errors"][:10]

    return RedirectResponse(
        url=f"/admin/products?excel_imported=1&created={result['created']}&updated={result['updated']}&failed={result['failed']}",
        status_code=303
    )

# ==================== 선택 항목 일괄 작업 (삭제, 가격변경, 카테고리변경) ====================
@router.post("/products/bulk-delete")
async def admin_bulk_delete_products(
    request: Request,
    product_ids: str = Form(...)
):
    """선택 상품 일괄 삭제 (소프트 삭제)"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    ids = [int(x.strip()) for x in product_ids.split(",") if x.strip().isdigit()]
    count = queries.bulk_delete_products_admin(ids)
    return RedirectResponse(url=f"/admin/products?bulk_deleted=1&count={count}", status_code=303)

@router.post("/products/bulk-price")
async def admin_bulk_update_prices(
    request: Request,
    product_ids: str = Form(...),
    price_type: str = Form(...),
    price_value: float = Form(...)
):
    """선택 상품 가격 일괄 변경"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    ids = [int(x.strip()) for x in product_ids.split(",") if x.strip().isdigit()]
    count = queries.bulk_update_product_prices(ids, mode=price_type, value=price_value)
    return RedirectResponse(url=f"/admin/products?bulk_price_updated=1&count={count}", status_code=303)

@router.post("/products/bulk-category")
async def admin_bulk_update_category(
    request: Request,
    product_ids: str = Form(...),
    target_category_id: int = Form(...)
):
    """선택 상품 카테고리 일괄 이동"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    ids = [int(x.strip()) for x in product_ids.split(",") if x.strip().isdigit()]
    count = queries.bulk_update_product_category(ids, target_category_id)
    return RedirectResponse(url=f"/admin/products?bulk_category_updated=1&count={count}", status_code=303)

@router.post("/products/{product_id}/price")
async def admin_quick_update_price(
    request: Request,
    product_id: int,
    price: int = Form(...)
):
    """상품 가격 즉시 수정"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    queries.update_product_price(product_id, price)
    return RedirectResponse(url="/admin/products?updated=1", status_code=303)

@router.get("/products/new", response_class=HTMLResponse)
async def admin_product_new_page(request: Request):
    """새 상품 등록 폼"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin/product_form.html",
        context=admin_context(request, admin, {
            "product": None,
            "title": f"새 카렌다 상품 등록 - {settings.COMPANY_NAME}"
        })
    )

@router.post("/products/new")
async def admin_create_product(
    request: Request,
    category_id: int = Form(...),
    item_code: str = Form(...),
    name: str = Form(...),
    price: int = Form(0),
    dimensions: str = Form(""),
    sheets: str = Form(""),
    paper_type: str = Form(""),
    binding: str = Form(""),
    imprint_size: str = Form(""),
    description: str = Form(""),
    thumbnail_url: str = Form("")
):
    """새 상품 저장"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    queries.create_product_admin(
        category_id=category_id,
        item_code=item_code,
        name=name,
        price=price,
        dimensions=dimensions,
        sheets=sheets,
        paper_type=paper_type,
        binding=binding,
        imprint_size=imprint_size,
        description=description,
        thumbnail_url=thumbnail_url
    )
    return RedirectResponse(url="/admin/products?created=1", status_code=303)

@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def admin_product_edit_page(request: Request, product_id: int):
    """상품 상세 수정 폼"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    product = queries.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    return templates.TemplateResponse(
        request=request,
        name="admin/product_form.html",
        context=admin_context(request, admin, {
            "product": product,
            "title": f"상품 수정 ({product['name']}) - {settings.COMPANY_NAME}"
        })
    )

@router.post("/products/{product_id}/edit")
async def admin_update_product(
    request: Request,
    product_id: int,
    category_id: int = Form(...),
    item_code: str = Form(...),
    name: str = Form(...),
    price: int = Form(0),
    dimensions: str = Form(""),
    sheets: str = Form(""),
    paper_type: str = Form(""),
    binding: str = Form(""),
    imprint_size: str = Form(""),
    description: str = Form(""),
    thumbnail_url: str = Form("")
):
    """상품 수정 저장"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    queries.update_product_full(
        product_id=product_id,
        category_id=category_id,
        item_code=item_code,
        name=name,
        price=price,
        dimensions=dimensions,
        sheets=sheets,
        paper_type=paper_type,
        binding=binding,
        imprint_size=imprint_size,
        description=description,
        thumbnail_url=thumbnail_url
    )
    return RedirectResponse(url="/admin/products?updated=1", status_code=303)

@router.post("/products/{product_id}/delete")
async def admin_delete_product(request: Request, product_id: int):
    """상품 비활성화 (삭제)"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    queries.delete_product_admin(product_id)
    return RedirectResponse(url="/admin/products?deleted=1", status_code=303)

# ==================== Q&A 답변 관리 ====================
@router.get("/qna", response_class=HTMLResponse)
async def admin_qna_list(request: Request, page: int = Query(1, ge=1)):
    """Q&A 질문 관리 목록"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    posts, total = queries.get_qna_posts(page=page, per_page=15)
    return templates.TemplateResponse(
        request=request,
        name="admin/qna_list.html",
        context=admin_context(request, admin, {
            "posts": posts,
            "total": total,
            "current_page": page,
            "title": f"Q&A 질문 및 답변 관리 - {settings.COMPANY_NAME}"
        })
    )

@router.post("/qna/{qna_id}/reply")
async def admin_reply_qna(
    request: Request,
    qna_id: int,
    admin_answer: str = Form(...)
):
    """Q&A 질문 답변 등록"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    queries.update_qna_reply(qna_id, admin_answer)
    return RedirectResponse(url="/admin/qna?replied=1", status_code=303)

# ==================== 견적 문의 관리 ====================
@router.get("/quotes", response_class=HTMLResponse)
async def admin_quotes_list(request: Request, page: int = Query(1, ge=1)):
    """견적 문의 관리 목록"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    quotes = queries.get_quotes(limit=20, offset=(page - 1) * 20)
    return templates.TemplateResponse(
        request=request,
        name="admin/quotes_list.html",
        context=admin_context(request, admin, {
            "quotes": quotes,
            "title": f"온라인 견적 문의 관리 - {settings.COMPANY_NAME}"
        })
    )

@router.post("/quotes/{quote_id}/update")
async def admin_update_quote(
    request: Request,
    quote_id: int,
    status: str = Form(...),
    admin_reply: Optional[str] = Form(None)
):
    """견적 문의 상태 및 메모 수정"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    queries.update_quote_status(quote_id, status, admin_reply)
    return RedirectResponse(url="/admin/quotes?updated=1", status_code=303)

# ==================== 공지사항 관리 ====================
@router.get("/notices", response_class=HTMLResponse)
async def admin_notices_list(request: Request):
    """공지사항 관리"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    posts = queries.get_posts(board_type="notice", limit=30)
    return templates.TemplateResponse(
        request=request,
        name="admin/notices_list.html",
        context=admin_context(request, admin, {
            "posts": posts,
            "title": f"공지사항 관리 - {settings.COMPANY_NAME}"
        })
    )

@router.post("/notices/new")
async def admin_create_notice(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    is_pinned: Optional[str] = Form(None)
):
    """공지사항 등록"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    pinned = True if is_pinned == "on" or is_pinned == "true" else False
    queries.create_notice_admin(title, content, pinned)
    return RedirectResponse(url="/admin/notices?created=1", status_code=303)

@router.post("/notices/{post_id}/delete")
async def admin_delete_notice(request: Request, post_id: int):
    """공지사항 삭제"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    queries.delete_notice_admin(post_id)
    return RedirectResponse(url="/admin/notices?deleted=1", status_code=303)

# ==================== 사용자 및 권한 관리 (User Management) ====================
@router.get("/users", response_class=HTMLResponse)
async def admin_users_list(request: Request):
    """관리자/사용자 계정 및 권한 관리 목록"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    if not has_permission(admin, "users"):
        raise HTTPException(status_code=403, detail="사용자 관리 접근 권한이 없습니다.")

    users = queries.get_all_admins()
    user_error = request.session.pop("user_error", None)

    return templates.TemplateResponse(
        request=request,
        name="admin/users_list.html",
        context=admin_context(request, admin, {
            "users": users,
            "user_error": user_error,
            "title": f"사용자 및 권한 관리 - {settings.COMPANY_NAME}"
        })
    )

@router.post("/users/new")
async def admin_create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    role: str = Form("sub_admin"),
    permissions: List[str] = Form([]),
    phone: str = Form(""),
    email: str = Form("")
):
    """신규 관리자/사용자 계정 생성"""
    admin = get_current_admin(request)
    if not admin or not has_permission(admin, "users"):
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

    clean_username = username.strip()
    if not clean_username or len(clean_username) < 3:
        request.session["user_error"] = "아이디는 3자 이상 입력해주세요."
        return RedirectResponse(url="/admin/users?error=1", status_code=303)

    if queries.get_admin_by_username(clean_username):
        request.session["user_error"] = f"'{clean_username}' 아이디는 이미 등록되어 있습니다."
        return RedirectResponse(url="/admin/users?error=1", status_code=303)

    if not password or len(password) < 4:
        request.session["user_error"] = "비밀번호는 최소 4자 이상이어야 합니다."
        return RedirectResponse(url="/admin/users?error=1", status_code=303)

    if role == "super_admin":
        perm_str = "all,products,quotes,qna,notices,users"
    else:
        perm_str = ",".join(permissions) if permissions else "products"

    queries.create_admin_user(
        username=clean_username,
        password=password,
        name=name.strip(),
        role=role,
        permissions=perm_str,
        phone=phone.strip(),
        email=email.strip()
    )
    return RedirectResponse(url="/admin/users?created=1", status_code=303)

@router.post("/users/{user_id}/edit")
async def admin_update_user(
    request: Request,
    user_id: int,
    name: str = Form(...),
    role: str = Form("sub_admin"),
    permissions: List[str] = Form([]),
    phone: str = Form(""),
    email: str = Form(""),
    is_active: Optional[str] = Form(None)
):
    """사용자 정보 및 권한 수정"""
    admin = get_current_admin(request)
    if not admin or not has_permission(admin, "users"):
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

    target = queries.get_admin_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")

    # 본인 계정 비활성화 방지
    active_bool = True if is_active == "on" or is_active == "true" else False
    if target["id"] == admin["id"]:
        active_bool = True

    if role == "super_admin":
        perm_str = "all,products,quotes,qna,notices,users"
    else:
        perm_str = ",".join(permissions) if permissions else ""

    queries.update_admin_user(
        admin_id=user_id,
        name=name.strip(),
        role=role,
        permissions=perm_str,
        phone=phone.strip(),
        email=email.strip(),
        is_active=active_bool
    )
    return RedirectResponse(url="/admin/users?updated=1", status_code=303)

@router.post("/users/{user_id}/password")
async def admin_change_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...)
):
    """관리자 비밀번호 재설정/변경"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    # 다른 사람의 비밀번호를 바꾸려면 users 권한 필요, 본인 비밀번호는 본인 허용
    if admin["id"] != user_id and not has_permission(admin, "users"):
        raise HTTPException(status_code=403, detail="비밀번호 변경 권한이 없습니다.")

    if not new_password or len(new_password) < 4:
        request.session["user_error"] = "비밀번호는 최소 4자 이상이어야 합니다."
        return RedirectResponse(url="/admin/users?error=1", status_code=303)

    queries.update_admin_password(user_id, new_password)
    return RedirectResponse(url="/admin/users?pwd_updated=1", status_code=303)

@router.post("/users/{user_id}/delete")
async def admin_delete_user(
    request: Request,
    user_id: int
):
    """관리자 계정 삭제"""
    admin = get_current_admin(request)
    if not admin or not has_permission(admin, "users"):
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

    if user_id == admin["id"]:
        request.session["user_error"] = "현재 로그인 중인 본인 계정은 삭제할 수 없습니다."
        return RedirectResponse(url="/admin/users?error=1", status_code=303)

    if user_id == 1:
        request.session["user_error"] = "기본 대표관리자 계정(ID: 1)은 삭제할 수 없습니다."
        return RedirectResponse(url="/admin/users?error=1", status_code=303)

    queries.delete_admin_user(user_id)
    return RedirectResponse(url="/admin/users?deleted=1", status_code=303)
