import os
import re
import urllib.request
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_PRODUCTS_DIR = BASE_DIR / "app" / "static" / "products"
STATIC_PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# SSL 검증 우회 컨텍스트 생성 (self-signed cert 대응)
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def download_image(url: str, target_path: Path) -> bool:
    if target_path.exists() and target_path.stat().st_size > 0:
        return True
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as response:
            content = response.read()
            if content:
                target_path.write_bytes(content)
                return True
    except Exception as e:
        print(f"  [다운로드 실패] {url} -> {e}")
    return False

def get_filename_from_url(url: str) -> str:
    # URL에서 마지막 파일명 추출 (쿼리 스트링 제거)
    clean_url = url.split("?")[0].split("#")[0]
    filename = clean_url.rstrip("/").split("/")[-1]
    # 특수문자 안전 처리
    filename = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)
    if not filename or "." not in filename:
        filename = f"img_{abs(hash(url))}.jpg"
    return filename

def main():
    if not DATABASE_URL:
        print("DATABASE_URL 환경 변수가 없습니다.")
        return

    print("Neon DB 연결 중...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1. product_images 목록 조회
    cur.execute("SELECT id, image_url FROM product_images;")
    product_images = cur.fetchall()

    # 2. products 목록 조회
    cur.execute("SELECT id, thumbnail_url FROM products;")
    products = cur.fetchall()

    # 다운로드할 고유 URL 목록 수집
    urls_to_download = {}
    for _, img_url in product_images:
        if img_url and img_url.startswith("http"):
            filename = get_filename_from_url(img_url)
            urls_to_download[img_url] = filename

    for _, thumb_url in products:
        if thumb_url and thumb_url.startswith("http"):
            filename = get_filename_from_url(thumb_url)
            urls_to_download[thumb_url] = filename

    print(f"총 다운로드 대상 이미지: {len(urls_to_download)}개")

    # 병렬 다운로드 실행
    downloaded_count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {
            executor.submit(download_image, url, STATIC_PRODUCTS_DIR / fname): (url, fname)
            for url, fname in urls_to_download.items()
        }
        for future in as_completed(future_to_url):
            url, fname = future_to_url[future]
            try:
                success = future.result()
                if success:
                    downloaded_count += 1
            except Exception as e:
                print(f"Error processing {url}: {e}")

    print(f"이미지 다운로드 완료: {downloaded_count}/{len(urls_to_download)}개 성공")

    # 3. DB 경로 업데이트 (/static/products/파일명)
    print("\nDB 이미지 경로 업데이트 시작...")

    updated_images = 0
    for img_id, img_url in product_images:
        if img_url and img_url.startswith("http"):
            filename = get_filename_from_url(img_url)
            local_path = f"/static/products/{filename}"
            cur.execute("UPDATE product_images SET image_url = %s WHERE id = %s;", (local_path, img_id))
            updated_images += 1

    updated_thumbs = 0
    for prod_id, thumb_url in products:
        if thumb_url and thumb_url.startswith("http"):
            filename = get_filename_from_url(thumb_url)
            local_path = f"/static/products/{filename}"
            cur.execute("UPDATE products SET thumbnail_url = %s WHERE id = %s;", (local_path, prod_id))
            updated_thumbs += 1

    conn.commit()
    print(f"DB 업데이트 완료: product_images {updated_images}건, products {updated_thumbs}건")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
