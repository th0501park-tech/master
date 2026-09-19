import os
import re
import urllib.request
from bs4 import BeautifulSoup
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 사이트 class_id 와 DB slug 매핑
CATEGORY_MAP = {
    1: "large-calendar",       # 대형카렌다
    20: "korea-landscape",     # 국내풍경
    21: "world-landscape",     # 세계풍경
    22: "illustration-kids",   # 일러스트/아동
    23: "paintings",           # 동양화/서양화/수채화
    24: "sports-flowers",      # 스포츠/꽃/미녀
    25: "traditional-hanbok",  # 전통/한복
    31: "house-health",        # 주택/건강
    13: "number-board",        # 숫자판
    8: "desk-large",           # 대형 탁상용(내지)
    9: "desk-inner",           # 탁상용(내지)
    10: "desk-gold",           # 탁상용(금박)
    42: "daily-weekly",        # 일력/주력
    45: "desk-gold-budget",    # 탁상용(금박) 저가용
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_html(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("cp949", errors="replace")
    except Exception as e:
        print(f"  [오류] URL 요청 실패 ({url}): {e}")
        return None

def parse_product_detail(item_url):
    html = fetch_html(item_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    
    # 1. 이미지 추출
    images = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "/item/" in src and src.endswith((".jpg", ".png", ".gif")):
            if not src.startswith("http"):
                src = "http://www.bosungcalendar.com/bs/" + src.lstrip("/")
            if src not in images:
                images.append(src)

    # 2. 텍스트 정보 파싱
    page_text = soup.get_text()
    
    # 제목 파싱: "현재위치: HOME > ... > [코드 상품명]" 패턴 찾기
    title_match = re.search(r"현재위치:\s*HOME\s*>\s*[^>\n]+\s*>\s*([^\n\r]+)", page_text)
    full_title = title_match.group(1).strip() if title_match else ""
    
    item_code = ""
    name = full_title
    if full_title:
        code_match = re.match(r"^([A-Za-z0-9\-_]+)\s+(.+)$", full_title)
        if code_match:
            item_code = code_match.group(1).strip()
            name = code_match.group(2).strip()

    # 정가 추출
    price = 0
    price_match = re.search(r"정가\s*:\s*([0-9,]+)원", page_text)
    if price_match:
        price = int(price_match.group(1).replace(",", ""))

    # 규격 및 매수
    dimensions = ""
    sheets = ""
    dim_match = re.search(r"규격\s*:\s*([^\n\r|]+)", page_text)
    if dim_match:
        dim_text = dim_match.group(1).strip()
        sheets_match = re.search(r"X\s*(\d+매)", dim_text)
        if sheets_match:
            sheets = sheets_match.group(1).strip()
            dim_text = re.sub(r"X\s*\d+매", "", dim_text).strip()
        dimensions = dim_text

    # 용지 / 지질
    paper_type = ""
    paper_match = re.search(r"용지\s*:\s*([^\n\r|]+)", page_text)
    if paper_match:
        paper_type = paper_match.group(1).strip()

    # 제본
    binding = ""
    bind_match = re.search(r"제본\s*:\s*([^\n\r|]+)", page_text)
    if bind_match:
        binding = bind_match.group(1).strip()

    # 상호란
    imprint_size = ""
    imp_match = re.search(r"상호란\s*:\s*([^\n\r|]+)", page_text)
    if imp_match:
        imprint_size = imp_match.group(1).strip()

    # 상품 상세 설명
    description = ""
    desc_match = re.search(r"상품상세설명\s*(.*?)\s*결제/배송/반품/환불", page_text, re.S)
    if desc_match:
        raw_desc = desc_match.group(1).strip()
        clean_desc = re.sub(r"\s+", " ", raw_desc)
        description = clean_desc

    thumbnail_url = images[0] if images else ""

    return {
        "item_code": item_code,
        "name": name or full_title or "카렌다 상품",
        "price": price,
        "dimensions": dimensions,
        "sheets": sheets,
        "paper_type": paper_type,
        "binding": binding,
        "imprint_size": imprint_size,
        "description": description,
        "thumbnail_url": thumbnail_url,
        "images": images
    }

def run_import():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1. DB에 등록된 카테고리 매핑 가져오기 (slug -> id)
    cur.execute("SELECT slug, id, name FROM categories;")
    db_cats = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

    total_inserted = 0
    total_images_inserted = 0

    print("=== 보성문화카렌다사 실제 상품 수집 및 DB 저장 시작 ===")

    for class_id, slug in CATEGORY_MAP.items():
        if slug not in db_cats:
            continue
        cat_id, cat_name = db_cats[slug]
        print(f"\n📂 [{cat_name}] (class_id={class_id}) 상품 탐색 중...")

        list_url = f"http://www.bosungcalendar.com/bs/shop/index.php?page=view_class&class_id={class_id}"
        html = fetch_html(list_url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        # 상품 상세 링크 찾기
        item_links = []
        for a in soup.find_all("a", href=re.compile(r"page=view_item")):
            href = a.get("href")
            # item_id 추출
            m = re.search(r"item_id=(\d+)", href)
            if m:
                item_id = m.group(1)
                full_item_url = f"http://www.bosungcalendar.com/bs/shop/index.php?page=view_item&class_id=,{class_id},&item_id={item_id}"
                if full_item_url not in item_links:
                    item_links.append(full_item_url)

        print(f"  -> {len(item_links)}개 상품 발견. 상위 2개 상품을 상세 수집합니다.")

        # 카테고리당 최대 2개 상품씩 샘플 수집 (약 20~28개 대표 상품)
        for item_url in item_links[:2]:
            product = parse_product_detail(item_url)
            if not product or not product["name"]:
                continue

            # 중복 체크
            cur.execute("SELECT id FROM products WHERE item_code = %s AND category_id = %s;", 
                        (product["item_code"], cat_id))
            row = cur.fetchone()
            if row:
                prod_id = row[0]
                print(f"    [기존] {product['item_code']} {product['name']} (ID: {prod_id})")
            else:
                insert_prod_sql = """
                INSERT INTO products (
                    category_id, item_code, name, price, dimensions, 
                    sheets, paper_type, binding, imprint_size, 
                    description, thumbnail_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """
                cur.execute(insert_prod_sql, (
                    cat_id, product["item_code"], product["name"], product["price"],
                    product["dimensions"], product["sheets"], product["paper_type"],
                    product["binding"], product["imprint_size"], product["description"],
                    product["thumbnail_url"]
                ))
                prod_id = cur.fetchone()[0]
                total_inserted += 1
                print(f"    [신규] {product['item_code']} {product['name']} ({product['price']:,}원) -> DB ID: {prod_id}")

            # 이미지 저장
            for idx, img_url in enumerate(product["images"]):
                # 월 번호 추정: _m_0.jpg(표지), _m_1.jpg(1월) ...
                month_match = re.search(r"_m_(\d+)\.", img_url)
                month = int(month_match.group(1)) if month_match else idx
                title = "표지" if month == 0 else f"{month}월"

                cur.execute("""
                    INSERT INTO product_images (product_id, image_url, page_month, title, sort_order)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (prod_id, img_url, month, title, month))
                total_images_inserted += 1

        conn.commit()

    print("\n==========================================")
    print(f"🎉 상품 데이터 적재 완료!")
    print(f"- 새로 등록된 상품 수: {total_inserted}개")
    print(f"- 등록된 상품 이미지 수: {total_images_inserted}개")

    # DB 전체 현황 출력
    cur.execute("SELECT COUNT(*) FROM products;")
    total_prods = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM product_images;")
    total_imgs = cur.fetchone()[0]
    print(f"- 현재 DB 총 상품 수: {total_prods}개")
    print(f"- 현재 DB 총 이미지 수: {total_imgs}개")

    cur.close()
    conn.close()

if __name__ == "__main__":
    run_import()
