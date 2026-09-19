from typing import List, Dict, Any, Optional
from app.db.connection import get_db

def get_categories() -> List[Dict[str, Any]]:
    """모든 활성 카테고리 목록 조회 (정렬순)"""
    with get_db() as cur:
        cur.execute("""
            SELECT c.*, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id AND p.is_active = TRUE
            WHERE c.is_active = TRUE
            GROUP BY c.id
            ORDER BY c.sort_order ASC;
        """)
        return cur.fetchall()

def get_category_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """슬러그로 카테고리 단건 조회"""
    with get_db() as cur:
        cur.execute("SELECT * FROM categories WHERE slug = %s AND is_active = TRUE;", (slug,))
        return cur.fetchone()

def get_featured_products(limit: int = 8) -> List[Dict[str, Any]]:
    """메인 페이지 추천/베스트 상품 목록"""
    with get_db() as cur:
        cur.execute("""
            SELECT p.*, c.name as category_name, c.slug as category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE
            ORDER BY p.id ASC
            LIMIT %s;
        """, (limit,))
        return cur.fetchall()

def get_products_by_category(
    category_id: int, 
    search: Optional[str] = None, 
    sort: str = "newest",
    page: int = 1, 
    per_page: int = 12
) -> tuple[List[Dict[str, Any]], int]:
    """카테고리별 상품 목록 페이징 조회"""
    offset = (page - 1) * per_page
    params: List[Any] = [category_id]
    where_clauses = ["p.category_id = %s", "p.is_active = TRUE"]

    if search:
        where_clauses.append("(p.name ILIKE %s OR p.item_code ILIKE %s)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param])

    order_by = "p.id DESC"
    if sort == "price_asc":
        order_by = "p.price ASC"
    elif sort == "price_desc":
        order_by = "p.price DESC"
    elif sort == "name":
        order_by = "p.name ASC"

    where_sql = " AND ".join(where_clauses)

    with get_db() as cur:
        # 전체 개수
        count_sql = f"SELECT COUNT(*) as total FROM products p WHERE {where_sql};"
        cur.execute(count_sql, tuple(params))
        total = cur.fetchone()["total"]

        # 페이징 목록
        list_sql = f"""
            SELECT p.*, c.name as category_name, c.slug as category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE {where_sql}
            ORDER BY {order_by}
            LIMIT %s OFFSET %s;
        """
        list_params = params + [per_page, offset]
        cur.execute(list_sql, tuple(list_params))
        items = cur.fetchall()

    return items, total

def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """상품 상세 및 월별 이미지 전체 조회"""
    with get_db() as cur:
        cur.execute("""
            SELECT p.*, c.name as category_name, c.slug as category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s AND p.is_active = TRUE;
        """, (product_id,))
        product = cur.fetchone()

        if not product:
            return None

        # 월별 이미지 목록 조회
        cur.execute("""
            SELECT * FROM product_images
            WHERE product_id = %s
            ORDER BY page_month ASC, sort_order ASC;
        """, (product_id,))
        product["images"] = cur.fetchall()

        return product

def search_products(query: str, limit: int = 24) -> List[Dict[str, Any]]:
    """전체 상품 검색 (상품코드, 상품명)"""
    with get_db() as cur:
        search_param = f"%{query}%"
        cur.execute("""
            SELECT p.*, c.name as category_name, c.slug as category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE 
              AND (p.name ILIKE %s OR p.item_code ILIKE %s OR p.description ILIKE %s)
            ORDER BY p.id ASC
            LIMIT %s;
        """, (search_param, search_param, search_param, limit))
        return cur.fetchall()

def create_quote(
    author_name: str,
    phone: str,
    title: str,
    content: str,
    product_id: Optional[int] = None,
    inquiry_type: str = "견적문의",
    email: Optional[str] = None,
    quantity: Optional[int] = None,
    password: Optional[str] = None,
    file_url: Optional[str] = None
) -> int:
    """견적/구매 문의 작성"""
    with get_db() as cur:
        cur.execute("""
            INSERT INTO quotes (
                product_id, inquiry_type, author_name, phone, email,
                quantity, title, content, password, file_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            product_id, inquiry_type, author_name, phone, email,
            quantity, title, content, password, file_url
        ))
        return cur.fetchone()["id"]

def get_quotes(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """견적/문의 게시판 목록 조회"""
    with get_db() as cur:
        cur.execute("""
            SELECT q.id, q.inquiry_type, q.author_name, q.title, q.quantity,
                   q.status, q.created_at, q.password, p.name as product_name
            FROM quotes q
            LEFT JOIN products p ON q.product_id = p.id
            ORDER BY q.created_at DESC
            LIMIT %s OFFSET %s;
        """, (limit, offset))
        return cur.fetchall()

def get_quote_by_id(quote_id: int) -> Optional[Dict[str, Any]]:
    """견적/문의 단건 상세 조회"""
    with get_db() as cur:
        cur.execute("""
            SELECT q.*, p.name as product_name, p.item_code
            FROM quotes q
            LEFT JOIN products p ON q.product_id = p.id
            WHERE q.id = %s;
        """, (quote_id,))
        return cur.fetchone()

def get_posts(board_type: str = "notice", limit: int = 5) -> List[Dict[str, Any]]:
    """게시판(공지사항 등) 목록 조회"""
    with get_db() as cur:
        cur.execute("""
            SELECT * FROM posts
            WHERE board_type = %s
            ORDER BY is_pinned DESC, created_at DESC
            LIMIT %s;
        """, (board_type, limit))
        return cur.fetchall()

def get_notices_paginated(page: int = 1, per_page: int = 10) -> tuple[List[Dict[str, Any]], int]:
    """공지사항 페이징 목록 조회"""
    offset = (page - 1) * per_page
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) as total FROM posts WHERE board_type = 'notice';")
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT * FROM posts
            WHERE board_type = 'notice'
            ORDER BY is_pinned DESC, id DESC
            LIMIT %s OFFSET %s;
        """, (per_page, offset))
        posts = cur.fetchall()
        return posts, total

def get_notice_by_id(post_id: int) -> Optional[Dict[str, Any]]:
    """공지사항 단건 상세 조회 및 조회수 증가"""
    with get_db() as cur:
        cur.execute("UPDATE posts SET views = views + 1 WHERE id = %s AND board_type = 'notice';", (post_id,))
        cur.execute("SELECT * FROM posts WHERE id = %s AND board_type = 'notice';", (post_id,))
        return cur.fetchone()

# ==================== FAQ 쿼리 ====================
def get_faqs(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """FAQ 목록 조회 (카테고리 필터링 지원)"""
    with get_db() as cur:
        if category and category != "전체":
            cur.execute("""
                SELECT * FROM faqs
                WHERE is_active = TRUE AND category = %s
                ORDER BY sort_order ASC, id ASC;
            """, (category,))
        else:
            cur.execute("""
                SELECT * FROM faqs
                WHERE is_active = TRUE
                ORDER BY sort_order ASC, id ASC;
            """)
        return cur.fetchall()

def get_faq_categories() -> List[str]:
    """FAQ 카테고리 목록 조회"""
    with get_db() as cur:
        cur.execute("SELECT DISTINCT category FROM faqs WHERE is_active = TRUE ORDER BY category ASC;")
        return [row["category"] for row in cur.fetchall()]

# ==================== Q&A (질문과 답변) 쿼리 ====================
def get_qna_posts(
    category: Optional[str] = None, 
    search: Optional[str] = None, 
    page: int = 1, 
    per_page: int = 10
) -> tuple[List[Dict[str, Any]], int]:
    """Q&A 게시판 목록 페이징 조회"""
    offset = (page - 1) * per_page
    where_clauses = ["1=1"]
    params: List[Any] = []

    if category and category != "전체":
        where_clauses.append("category = %s")
        params.append(category)

    if search:
        where_clauses.append("(title ILIKE %s OR content ILIKE %s OR author ILIKE %s)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    where_sql = " AND ".join(where_clauses)

    with get_db() as cur:
        count_sql = f"SELECT COUNT(*) as total FROM qna_posts WHERE {where_sql};"
        cur.execute(count_sql, tuple(params))
        total = cur.fetchone()["total"]

        list_sql = f"""
            SELECT id, category, title, author, is_secret, views, status, 
                   admin_answer, answered_at, created_at
            FROM qna_posts
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT %s OFFSET %s;
        """
        list_params = params + [per_page, offset]
        cur.execute(list_sql, tuple(list_params))
        posts = cur.fetchall()

        return posts, total

def get_qna_by_id(qna_id: int) -> Optional[Dict[str, Any]]:
    """Q&A 질문 단건 조회 및 조회수 증가"""
    with get_db() as cur:
        cur.execute("UPDATE qna_posts SET views = views + 1 WHERE id = %s;", (qna_id,))
        cur.execute("SELECT * FROM qna_posts WHERE id = %s;", (qna_id,))
        return cur.fetchone()

def create_qna_post(
    category: str,
    title: str,
    content: str,
    author: str,
    password: str,
    is_secret: bool = True
) -> int:
    """새 Q&A 질문 등록"""
    with get_db() as cur:
        cur.execute("""
            INSERT INTO qna_posts (category, title, content, author, password, is_secret)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (category, title, content, author, password, is_secret))
        return cur.fetchone()["id"]

def verify_qna_password(qna_id: int, password: str) -> bool:
    """Q&A 비밀번호 일치 여부 확인"""
    with get_db() as cur:
        cur.execute("SELECT password FROM qna_posts WHERE id = %s;", (qna_id,))
        row = cur.fetchone()
        if not row:
            return False
        return row["password"] == password

def seed_sample_notices():
    """기존 보성카렌다의 대표 공지사항 초기 등록"""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM posts WHERE board_type = 'notice';")
        if cur.fetchone()["cnt"] == 0:
            notices = [
                ("2027년 카다로그 배부중 입니다.", "2027년도 신규 캘린더 카다로그가 발간되었습니다. 신청해 주시면 우편으로 발송해 드립니다.", True),
                ("2027년 카렌다 사전 견적 접수 안내", "대량 주문 및 특수 맞춤형 인쇄 견적을 접수하고 있습니다. 미리 주문하시면 조기 할인 혜택이 제공됩니다.", True),
                ("2026년 카렌다 주문 마감 및 배송 일정 안내", "2026년도 달력 배송 일정 및 잔여 수량 안내입니다.", False),
                ("상호 인쇄용 로고 파일(AI/PDF) 접수 안내", "인쇄 제작 시 일러스트레이터(AI) 벡터 파일 또는 고해상도 PDF 파일을 첨부해 주시면 더욱 선명한 인쇄가 가능합니다.", False),
            ]
            for title, content, pinned in notices:
                cur.execute("""
                    INSERT INTO posts (board_type, title, content, is_pinned)
                    VALUES ('notice', %s, %s, %s);
                """, (title, content, pinned))

# ==================== 관리자 (Admin) 쿼리 ====================
def authenticate_admin(username: str, password: str) -> Optional[Dict[str, Any]]:
    """관리자 로그인 인증"""
    from app.core.security import verify_password
    with get_db() as cur:
        cur.execute("SELECT * FROM admins WHERE username = %s;", (username,))
        admin = cur.fetchone()
        if not admin:
            return None
        if not admin.get("is_active", True):
            return None
        if verify_password(admin["password_hash"], password):
            cur.execute("UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE id = %s;", (admin["id"],))
            return admin
        return None

def get_admin_by_id(admin_id: int) -> Optional[Dict[str, Any]]:
    """관리자 단건 조회"""
    with get_db() as cur:
        cur.execute("""
            SELECT id, username, name, role, permissions, phone, email, is_active, last_login, created_at 
            FROM admins WHERE id = %s;
        """, (admin_id,))
        return cur.fetchone()

def get_dashboard_stats() -> Dict[str, Any]:
    """관리자 대시보드 통계 및 최근 내역 조회"""
    with get_db() as cur:
        # 상품 수
        cur.execute("SELECT COUNT(*) as cnt FROM products WHERE is_active = TRUE;")
        total_products = cur.fetchone()["cnt"]

        # 견적 현황
        cur.execute("SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE status = '대기') as pending FROM quotes;")
        q_stat = cur.fetchone()
        total_quotes = q_stat["total"]
        pending_quotes = q_stat["pending"]

        # Q&A 현황
        cur.execute("SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE status = '답변대기') as pending FROM qna_posts;")
        qna_stat = cur.fetchone()
        total_qna = qna_stat["total"]
        pending_qna = qna_stat["pending"]

        # 최근 견적문의 5건
        cur.execute("""
            SELECT q.id, q.inquiry_type, q.author_name, q.title, q.quantity, q.status, q.created_at,
                   p.name as product_name
            FROM quotes q
            LEFT JOIN products p ON q.product_id = p.id
            ORDER BY q.created_at DESC
            LIMIT 5;
        """)
        recent_quotes = cur.fetchall()

        # 최근 Q&A 5건
        cur.execute("""
            SELECT id, category, title, author, is_secret, status, created_at
            FROM qna_posts
            ORDER BY id DESC
            LIMIT 5;
        """)
        recent_qna = cur.fetchall()

        return {
            "total_products": total_products,
            "total_quotes": total_quotes,
            "pending_quotes": pending_quotes,
            "total_qna": total_qna,
            "pending_qna": pending_qna,
            "recent_quotes": recent_quotes,
            "recent_qna": recent_qna
        }

def get_all_products_admin(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    sort_by: str = "id",
    order: str = "asc"
) -> List[Dict[str, Any]]:
    """관리자용 전체 상품 목록 (정렬, 필터, 검색 지원)"""
    where_clauses = ["p.is_active = TRUE"]
    params: List[Any] = []

    if category_id:
        where_clauses.append("p.category_id = %s")
        params.append(category_id)

    if search:
        where_clauses.append("(p.name ILIKE %s OR p.item_code ILIKE %s)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param])

    where_sql = " AND ".join(where_clauses)

    sort_map = {
        "id": "p.id",
        "code": "p.item_code",
        "name": "p.name",
        "category": "c.name",
        "price": "p.price",
        "dimensions": "p.dimensions",
        "sheets": "p.sheets",
        "images": "image_count",
        "created_at": "p.created_at"
    }
    col = sort_map.get(sort_by.lower(), "p.id")
    direction = "DESC" if order.lower() == "desc" else "ASC"

    with get_db() as cur:
        cur.execute(f"""
            SELECT p.*, c.name as category_name,
                   (SELECT COUNT(*) FROM product_images WHERE product_id = p.id) as image_count
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE {where_sql}
            ORDER BY {col} {direction}, p.id ASC;
        """, tuple(params))
        return cur.fetchall()

def update_product_price(product_id: int, price: int):
    """상품 가격 빠른 수정"""
    with get_db() as cur:
        cur.execute("UPDATE products SET price = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;", (price, product_id))

def update_product_full(
    product_id: int,
    category_id: int,
    item_code: str,
    name: str,
    price: int,
    dimensions: str,
    sheets: str,
    paper_type: str,
    binding: str,
    imprint_size: str,
    description: str,
    thumbnail_url: str
):
    """상품 상세 전체 수정"""
    with get_db() as cur:
        cur.execute("""
            UPDATE products SET
                category_id = %s,
                item_code = %s,
                name = %s,
                price = %s,
                dimensions = %s,
                sheets = %s,
                paper_type = %s,
                binding = %s,
                imprint_size = %s,
                description = %s,
                thumbnail_url = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (
            category_id, item_code, name, price, dimensions,
            sheets, paper_type, binding, imprint_size, description,
            thumbnail_url, product_id
        ))

def create_product_admin(
    category_id: int,
    item_code: str,
    name: str,
    price: int,
    dimensions: str,
    sheets: str,
    paper_type: str,
    binding: str,
    imprint_size: str,
    description: str,
    thumbnail_url: str
) -> int:
    """관리자 신규 캘린더 상품 등록"""
    with get_db() as cur:
        cur.execute("""
            INSERT INTO products (
                category_id, item_code, name, price, dimensions,
                sheets, paper_type, binding, imprint_size, description, thumbnail_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            category_id, item_code, name, price, dimensions,
            sheets, paper_type, binding, imprint_size, description, thumbnail_url
        ))
        return cur.fetchone()["id"]

def delete_product_admin(product_id: int):
    """상품 비활성화(소프트 삭제)"""
    with get_db() as cur:
        cur.execute("UPDATE products SET is_active = FALSE WHERE id = %s;", (product_id,))

def bulk_delete_products_admin(product_ids: List[int]) -> int:
    """선택한 상품들 일괄 비활성화 (소프트 삭제)"""
    if not product_ids:
        return 0
    with get_db() as cur:
        cur.execute("""
            UPDATE products 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ANY(%s);
        """, (product_ids,))
        return cur.rowcount

def bulk_update_product_prices(product_ids: List[int], mode: str, value: float) -> int:
    """선택한 상품 가격 일괄 변경 (고정가, 금액가감, 비율가감)"""
    if not product_ids:
        return 0
    with get_db() as cur:
        if mode == "fixed":
            # 지정 금액으로 일괄 설정
            cur.execute("""
                UPDATE products
                SET price = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = ANY(%s) AND is_active = TRUE;
            """, (int(value), product_ids))
        elif mode == "add":
            # 금액 일괄 인상 (+원)
            cur.execute("""
                UPDATE products
                SET price = GREATEST(0, price + %s), updated_at = CURRENT_TIMESTAMP
                WHERE id = ANY(%s) AND is_active = TRUE;
            """, (int(value), product_ids))
        elif mode == "subtract":
            # 금액 일괄 인하 (-원)
            cur.execute("""
                UPDATE products
                SET price = GREATEST(0, price - %s), updated_at = CURRENT_TIMESTAMP
                WHERE id = ANY(%s) AND is_active = TRUE;
            """, (int(value), product_ids))
        elif mode == "percent_add":
            # 비율 일괄 인상 (+%), 10원 단위 반올림
            cur.execute("""
                UPDATE products
                SET price = ROUND((price * (1.0 + %s / 100.0)) / 10.0) * 10, updated_at = CURRENT_TIMESTAMP
                WHERE id = ANY(%s) AND is_active = TRUE;
            """, (float(value), product_ids))
        elif mode == "percent_sub":
            # 비율 일괄 인하 (-%), 10원 단위 반올림
            cur.execute("""
                UPDATE products
                SET price = GREATEST(0, ROUND((price * (1.0 - %s / 100.0)) / 10.0) * 10), updated_at = CURRENT_TIMESTAMP
                WHERE id = ANY(%s) AND is_active = TRUE;
            """, (float(value), product_ids))
        else:
            return 0
        return cur.rowcount

def bulk_update_product_category(product_ids: List[int], category_id: int) -> int:
    """선택한 상품 카테고리 일괄 이동"""
    if not product_ids:
        return 0
    with get_db() as cur:
        cur.execute("""
            UPDATE products
            SET category_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = ANY(%s) AND is_active = TRUE;
        """, (category_id, product_ids))
        return cur.rowcount

def upsert_product_excel(data: Dict[str, Any], update_existing: bool = True) -> str:
    """엑셀 일괄 등록용 상품 단건 Upsert"""
    item_code = data.get("item_code", "").strip()
    with get_db() as cur:
        cur.execute("SELECT id FROM products WHERE item_code = %s LIMIT 1;", (item_code,))
        existing = cur.fetchone()
        if existing:
            if not update_existing:
                return "skipped"
            cur.execute("""
                UPDATE products SET
                    category_id = %s,
                    name = %s,
                    price = %s,
                    dimensions = %s,
                    sheets = %s,
                    paper_type = %s,
                    binding = %s,
                    imprint_size = %s,
                    min_quantity = %s,
                    description = %s,
                    thumbnail_url = %s,
                    is_active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
            """, (
                data.get("category_id"),
                data.get("name"),
                data.get("price", 0),
                data.get("dimensions", ""),
                data.get("sheets", ""),
                data.get("paper_type", ""),
                data.get("binding", ""),
                data.get("imprint_size", ""),
                data.get("min_quantity", 100),
                data.get("description", ""),
                data.get("thumbnail_url", ""),
                existing["id"]
            ))
            return "updated"
        else:
            cur.execute("""
                INSERT INTO products (
                    category_id, item_code, name, price, dimensions,
                    sheets, paper_type, binding, imprint_size, min_quantity,
                    description, thumbnail_url, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id;
            """, (
                data.get("category_id"),
                item_code,
                data.get("name"),
                data.get("price", 0),
                data.get("dimensions", ""),
                data.get("sheets", ""),
                data.get("paper_type", ""),
                data.get("binding", ""),
                data.get("imprint_size", ""),
                data.get("min_quantity", 100),
                data.get("description", ""),
                data.get("thumbnail_url", "")
            ))
            return "created"

def update_qna_reply(qna_id: int, admin_answer: str):
    """Q&A 질문에 관리자 답변 등록 및 상태 '답변완료'로 변경"""
    with get_db() as cur:
        cur.execute("""
            UPDATE qna_posts SET
                admin_answer = %s,
                status = '답변완료',
                answered_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (admin_answer, qna_id))

def update_quote_status(quote_id: int, status: str, admin_reply: Optional[str] = None):
    """견적 문의 상태 및 관리자 메모/답변 수정"""
    with get_db() as cur:
        cur.execute("""
            UPDATE quotes SET
                status = %s,
                admin_reply = %s,
                replied_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (status, admin_reply, quote_id))

def create_notice_admin(title: str, content: str, is_pinned: bool = False) -> int:
    """공지사항 신규 등록"""
    with get_db() as cur:
        cur.execute("""
            INSERT INTO posts (board_type, title, content, is_pinned)
            VALUES ('notice', %s, %s, %s)
            RETURNING id;
        """, (title, content, is_pinned))
        return cur.fetchone()["id"]

def delete_notice_admin(post_id: int):
    """공지사항 삭제"""
    with get_db() as cur:
        cur.execute("DELETE FROM posts WHERE id = %s AND board_type = 'notice';", (post_id,))

# ==================== 관리자 계정 및 권한 관리 쿼리 ====================
def get_all_admins() -> List[Dict[str, Any]]:
    """모든 관리자 계정 목록 조회"""
    with get_db() as cur:
        cur.execute("""
            SELECT id, username, name, role, permissions, phone, email, is_active, last_login, created_at
            FROM admins
            ORDER BY id ASC;
        """)
        rows = cur.fetchall()
        for r in rows:
            r["created_at_str"] = r["created_at"].strftime("%Y-%m-%d %H:%M") if r.get("created_at") else "-"
            r["last_login_str"] = r["last_login"].strftime("%Y-%m-%d %H:%M") if r.get("last_login") else "기록 없음"
        return rows

def get_admin_by_username(username: str) -> Optional[Dict[str, Any]]:
    """아이디로 관리자 계정 단건 조회"""
    with get_db() as cur:
        cur.execute("""
            SELECT id, username, name, role, permissions, phone, email, is_active, last_login, created_at
            FROM admins
            WHERE username = %s;
        """, (username,))
        return cur.fetchone()

def create_admin_user(
    username: str,
    password: str,
    name: str,
    role: str = "sub_admin",
    permissions: str = "products,quotes,qna,notices",
    phone: str = "",
    email: str = ""
) -> int:
    """신규 관리자/사용자 계정 생성"""
    from app.core.security import hash_password
    pwd_hash = hash_password(password)
    with get_db() as cur:
        cur.execute("""
            INSERT INTO admins (username, password_hash, name, role, permissions, phone, email, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id;
        """, (username, pwd_hash, name, role, permissions, phone, email))
        return cur.fetchone()["id"]

def update_admin_user(
    admin_id: int,
    name: str,
    role: str,
    permissions: str,
    phone: str = "",
    email: str = "",
    is_active: bool = True
):
    """관리자 정보 및 권한 수정"""
    with get_db() as cur:
        cur.execute("""
            UPDATE admins SET
                name = %s,
                role = %s,
                permissions = %s,
                phone = %s,
                email = %s,
                is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (name, role, permissions, phone, email, is_active, admin_id))

def update_admin_password(admin_id: int, new_password: str):
    """관리자 비밀번호 변경/재설정"""
    from app.core.security import hash_password
    pwd_hash = hash_password(new_password)
    with get_db() as cur:
        cur.execute("""
            UPDATE admins SET
                password_hash = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (pwd_hash, admin_id))

def delete_admin_user(admin_id: int):
    """관리자 계정 삭제"""
    with get_db() as cur:
        cur.execute("DELETE FROM admins WHERE id = %s;", (admin_id,))


