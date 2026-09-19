import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

CREATE_TABLES_SQL = """
-- 1. 카테고리 테이블
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 상품 테이블 (달력 특화 스펙 포함)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    item_code VARCHAR(50),                     -- 예: LD01, WI001
    name VARCHAR(255) NOT NULL,                -- 상품명
    price INT DEFAULT 0,                       -- 기본 단가 / 정가
    dimensions VARCHAR(100),                   -- 규격 (예: 1,000mm X 700mm)
    sheets VARCHAR(50),                        -- 매수 (예: 13매, 7매)
    paper_type VARCHAR(100),                   -- 용지/지질 (예: 아트지 / 옵셋 4도)
    binding VARCHAR(100),                      -- 제본 (예: P.V.C 홀더, 스프링)
    imprint_size VARCHAR(100),                 -- 상호 인쇄란 규격 (예: 180mm X 50mm)
    min_quantity INT DEFAULT 100,              -- 최소 주문 수량
    description TEXT,                          -- 상세 설명
    thumbnail_url VARCHAR(500),                -- 대표 썸네일 이미지
    is_active BOOLEAN DEFAULT TRUE,            -- 판매/노출 여부
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 상품 이미지 테이블 (월별 내지 1~12월 지원)
CREATE TABLE IF NOT EXISTS product_images (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    page_month INT DEFAULT 0,                  -- 0: 표지, 1~12: 해당 월 내지
    title VARCHAR(100),                        -- 이미지 설명 (예: 1월 내지)
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. 견적 및 구매 문의 테이블 (B2B 인쇄 핵심)
CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE SET NULL,
    inquiry_type VARCHAR(50) DEFAULT '견적문의',  -- 견적문의, 구매문의, 인쇄문의 등
    author_name VARCHAR(100) NOT NULL,         -- 회사명 또는 신청자명
    phone VARCHAR(50) NOT NULL,                -- 연락처
    email VARCHAR(100),                        -- 이메일
    quantity INT,                              -- 예상 주문 수량
    title VARCHAR(255) NOT NULL,               -- 제목
    content TEXT NOT NULL,                     -- 문의 내용 (인쇄 문구 등)
    password VARCHAR(255),                     -- 비회원 비밀글 비밀번호
    file_url VARCHAR(500),                     -- 첨부파일 (로고 AI/PDF 등)
    status VARCHAR(50) DEFAULT '대기',          -- 대기, 상담중, 답변완료, 주문확정
    admin_reply TEXT,                          -- 관리자 답변 내용
    replied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. 게시판 테이블 (공지사항, FAQ, 이용안내)
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    board_type VARCHAR(50) NOT NULL DEFAULT 'notice', -- notice(공지), faq, qna
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(100) DEFAULT '관리자',
    views INT DEFAULT 0,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

# 보성카렌다 14개 기본 카테고리 초기 데이터
INITIAL_CATEGORIES = [
    ("대형카렌다", "large-calendar", 1),
    ("국내풍경", "korea-landscape", 2),
    ("세계풍경", "world-landscape", 3),
    ("일러스트/아동", "illustration-kids", 4),
    ("동양화/서양화/수채화", "paintings", 5),
    ("스포츠/꽃/미녀", "sports-flowers", 6),
    ("전통/한복", "traditional-hanbok", 7),
    ("주택/건강", "house-health", 8),
    ("숫자판", "number-board", 9),
    ("대형 탁상용(내지)", "desk-large", 10),
    ("탁상용(내지)", "desk-inner", 11),
    ("탁상용(금박)", "desk-gold", 12),
    ("일력/주력", "daily-weekly", 13),
    ("탁상용(금박) 저가용", "desk-gold-budget", 14),
]

def init_database():
    print("Neon DB 연결 중...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("테이블 생성 중...")
    cur.execute(CREATE_TABLES_SQL)
    conn.commit()
    print("✅ 테이블 생성 완료!")

    print("\n기본 카테고리 14종 초기 데이터 삽입 중...")
    insert_category_sql = """
    INSERT INTO categories (name, slug, sort_order)
    VALUES (%s, %s, %s)
    ON CONFLICT (slug) DO UPDATE
    SET name = EXCLUDED.name, sort_order = EXCLUDED.sort_order;
    """
    for name, slug, sort_order in INITIAL_CATEGORIES:
        cur.execute(insert_category_sql, (name, slug, sort_order))
    conn.commit()
    print("✅ 기본 카테고리 데이터 삽입 완료!")

    # 생성된 테이블 목록 조회
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print("\n[현재 생성된 public 테이블 목록]")
    for t in tables:
        print(f" - {t[0]}")

    # 카테고리 개수 조회
    cur.execute("SELECT count(*) FROM categories;")
    cat_count = cur.fetchone()[0]
    print(f"\n[등록된 카테고리 수]: {cat_count}개")

    cur.close()
    conn.close()

if __name__ == "__main__":
    init_database()
