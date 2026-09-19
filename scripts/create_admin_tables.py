import os
import hashlib
import secrets
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"{salt}:{h}"

CREATE_ADMIN_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) DEFAULT '최고관리자',
    role VARCHAR(20) DEFAULT 'super_admin',
    permissions TEXT DEFAULT 'all,products,quotes,qna,notices,users',
    phone VARCHAR(50),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

def init_admin():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("1. admins 테이블 생성 중...")
    cur.execute(CREATE_ADMIN_TABLE_SQL)
    conn.commit()
    print("✅ admins 테이블 생성 완료!")

    # 기본 관리자 계정 생성 (아이디: admin / 비밀번호: admin1234)
    print("\n2. 기본 관리자 계정 생성 중...")
    cur.execute("SELECT id FROM admins WHERE username = 'admin';")
    if not cur.fetchone():
        hashed = hash_password("admin1234")
        cur.execute("""
            INSERT INTO admins (username, password_hash, name, role)
            VALUES (%s, %s, %s, %s);
        """, ("admin", hashed, "대표관리자", "admin"))
        conn.commit()
        print("✅ 기본 관리자 계정 생성 완료!")
        print("   - 아이디: admin")
        print("   - 비밀번호: admin1234")
    else:
        print("ℹ️ 관리자 계정(admin)이 이미 존재합니다.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    init_admin()
