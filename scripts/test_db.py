import os
import psycopg2
from dotenv import load_dotenv

# .env 환경 변수 로드
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("Neon DB 연결 시도 중...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("SELECT version();")
    version = cur.fetchone()[0]

    cur.execute("SELECT current_database(), current_user, NOW();")
    db, user, now = cur.fetchone()

    print("\n✅ Neon DB 연결 성공!")
    print(f"- 데이터베이스: {db}")
    print(f"- 사용자: {user}")
    print(f"- 현재 서버 시간: {now}")
    print(f"- PostgreSQL 버전: {version.split(',')[0]}")

    cur.close()
    conn.close()

except Exception as e:
    print("\n❌ DB 연결 실패:")
    print(e)
