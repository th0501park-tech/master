import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory: /Users/소스/WEB_PROJECT
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from project root
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "보성문화카렌다"
    PROJECT_VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Directory Paths
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"

    # Business Info (보성문화카렌다사 실제 정보 매핑)
    COMPANY_NAME: str = "보성문화카렌다사"
    CEO_NAME: str = "박용제"
    BIZ_NUMBER: str = "137-15-65949"
    MAIL_ORDER_NUMBER: str = "중구 02947호"
    TEL: str = "02) 2277-4431"
    FAX: str = "02) 2277-4390"
    ADDRESS: str = "서울 중구 을지로3가 275 (동아B/D 201호)"
    EMAIL: str = "bosung@bosungcalendar.com"
    EMAIL_SECONDARY: str = "happy4431@hanmail.net"
    WEBHARD_URL: str = "http://www.webhard.co.kr"
    WEBHARD_ID: str = "bosung4431"
    WEBHARD_PW: str = "22774431"

settings = Settings()
