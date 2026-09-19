import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

CREATE_BOARD_TABLES_SQL = """
-- 1. FAQ (자주 묻는 질문) 테이블
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,            -- 주문/결제, 인쇄/시안, 배송/납기, 기타
    question VARCHAR(300) NOT NULL,           -- 질문
    answer TEXT NOT NULL,                     -- 답변
    sort_order INT DEFAULT 0,                 -- 정렬 순서
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Q&A (질문과 답변 게시판) 테이블
CREATE TABLE IF NOT EXISTS qna_posts (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) DEFAULT '일반문의',    -- 견적/단가, 인쇄/시안, 배송문의, 기타
    title VARCHAR(255) NOT NULL,              -- 질문 제목
    content TEXT NOT NULL,                    -- 질문 내용
    author VARCHAR(100) NOT NULL,             -- 작성자
    password VARCHAR(255) NOT NULL,           -- 비밀글 조회/수정 비밀번호
    is_secret BOOLEAN DEFAULT TRUE,           -- 비밀글 여부 (기본 비공개 보호)
    views INT DEFAULT 0,                      -- 조회수
    status VARCHAR(50) DEFAULT '답변대기',      -- 답변대기, 답변완료
    admin_answer TEXT,                        -- 관리자 답변 내용
    answered_at TIMESTAMP WITH TIME ZONE,     -- 답변 일시
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

# FAQ 초기 데이터
SAMPLE_FAQS = [
    ("주문/결제", "최소 주문 수량은 몇 부부터 가능한가요?", 
     "기본적으로 완제품 상호 인쇄 기준 100부부터 주문 제작이 가능합니다. 100부 미만의 소량 제작을 원하실 경우 기성 달력에 부착하는 방식 등으로 진행 가능하오니 고객센터(02-2277-4431)로 문의해 주시면 친절히 안내해 드립니다.", 1),
    
    ("인쇄/시안", "상호 인쇄 시 회사 로고 파일은 어떤 형식으로 보내야 하나요?", 
     "선명한 인쇄를 위해 일러스트레이터 벡터 파일(AI, EPS) 또는 인쇄용 고해상도 PDF(300dpi 이상)를 권장합니다. 벡터 파일이 없으신 경우 명함 사진이나 깨끗한 이미지(JPG, PNG)를 보내주시면 저희 디자인팀에서 인쇄 가능한 데이터로 무료 변환 및 시안을 작성해 드립니다.", 2),
    
    ("인쇄/시안", "금박 인쇄와 옵셋 먹1도 인쇄의 차이는 무엇인가요?", 
     "금박 인쇄는 열과 압력으로 금색 박을 찍어내어 반짝이는 고급스러운 광택이 나며, 주로 탁상용 달력 하단 삼각대 인쇄에 널리 사용됩니다. 옵셋 먹1도 인쇄는 검은색 잉크로 벽걸이 달력 하단 상호란에 글씨와 로고를 정밀하고 경제적으로 인쇄하는 방식입니다.", 3),
    
    ("배송/납기", "시안 확정 후 제작 및 배송까지 기간은 얼마나 걸리나요?", 
     "인쇄 시안 최종 컨펌일로부터 영업일 기준 통상 7~10일 정도 소요됩니다. 단, 캘린더 주문이 집중되는 10월 중순~12월 성수기에는 제작 공정이 혼잡하므로 원하시는 납기일보다 2~3주 여유 있게 주문하시는 것을 권장합니다.", 4),
    
    ("배송/납기", "배송 방법 및 배송비는 어떻게 책정되나요?", 
     "달력은 부피와 중량이 큰 인쇄물이므로 전용 화물 택배 또는 서울/경기권 퀵배송, 대량 주문 시 용달 화물로 안전하게 배송됩니다. 일정 수량(300부 이상) 주문 시 수도권 무료 배송 혜택을 제공해 드립니다.", 5),
    
    ("주문/결제", "전자세금계산서 발행이 가능한가요?", 
     "네, 당연히 가능합니다. 주문 시 사업자등록증 사본과 계산서 수신용 이메일을 알려주시면 제품 출고 및 결제 확인 후 국세청 전자세금계산서를 즉시 발행해 드립니다.", 6),
]

# Q&A 초기 샘플 질문/답변 데이터
SAMPLE_QNAS = [
    ("인쇄/시안", "로고 파일이 JPG로만 있는데 상호 인쇄가 가능한가요?", 
     "회사 로고 AI 파일이 없고 고화질 JPG 이미지 파일만 가지고 있는데 탁상용 달력에 금박으로 깔끔하게 인쇄될 수 있을까요?", 
     "김태형", "1234", True, 24, "답변완료", 
     "네, 고객님! 보내주신 JPG 해상도가 충분하다면 저희 디자인팀에서 금박 동판 제작이 가능한 벡터(AI) 라인으로 보정 및 시안을 무료로 제작해 드립니다. 주문서 접수 후 메일로 시안을 먼저 확인시켜 드리겠습니다."),
    
    ("견적/단가", "탁상용 캘린더 500부 제작 시 개별 OPP 포장도 포함인가요?", 
     "직원 및 거래처 배포용으로 500부 제작 예정입니다. 개별 비닐 봉투(OPP)나 선물용 종이봉투가 기본으로 포함되는지 궁금합니다.", 
     "박서준", "1234", True, 18, "답변완료", 
     "네, 고객님. 보성문화카렌다사의 모든 탁상용 달력 제품은 1권씩 배포하시기 편하도록 전용 OPP 비닐봉투가 무상으로 동봉됩니다. 고급 조립식 종이케이스 포장을 원하실 경우 권당 소정의 추가 비용으로 변경 가능합니다."),
    
    ("배송문의", "전국 각 지사 5곳으로 나누어 분할 배송이 가능한가요?", 
     "총 1,000부 주문 후 서울 본사 및 부산, 대구, 대전 지사로 각각 수량을 나누어 배송받고 싶습니다. 분할 배송이 지원되나요?", 
     "이지은", "1234", True, 7, "답변대기", None),
]

def init_board_tables():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("1. 게시판 테이블 (faqs, qna_posts) 생성 중...")
    cur.execute(CREATE_BOARD_TABLES_SQL)
    conn.commit()
    print("✅ 게시판 테이블 생성 완료!")

    # FAQ 시드 데이터
    print("\n2. FAQ 초기 데이터 시딩 중...")
    cur.execute("SELECT COUNT(*) FROM faqs;")
    if cur.fetchone()[0] == 0:
        for cat, q, a, order in SAMPLE_FAQS:
            cur.execute("""
                INSERT INTO faqs (category, question, answer, sort_order)
                VALUES (%s, %s, %s, %s);
            """, (cat, q, a, order))
        conn.commit()
        print(f"✅ FAQ 샘플 데이터 {len(SAMPLE_FAQS)}건 삽입 완료!")
    else:
        print("ℹ️ FAQ 데이터가 이미 존재합니다.")

    # Q&A 시드 데이터
    print("\n3. Q&A 게시판 샘플 데이터 시딩 중...")
    cur.execute("SELECT COUNT(*) FROM qna_posts;")
    if cur.fetchone()[0] == 0:
        for cat, title, content, author, pw, is_sec, views, status, ans in SAMPLE_QNAS:
            cur.execute("""
                INSERT INTO qna_posts (
                    category, title, content, author, password, is_secret, 
                    views, status, admin_answer, answered_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP);
            """, (cat, title, content, author, pw, is_sec, views, status, ans))
        conn.commit()
        print(f"✅ Q&A 샘플 질문 {len(SAMPLE_QNAS)}건 삽입 완료!")
    else:
        print("ℹ️ Q&A 데이터가 이미 존재합니다.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    init_board_tables()
