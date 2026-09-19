# 보성문화카렌다 웹 쇼핑몰 (Python + Neon DB)

기존 레거시 쇼핑몰([보성문화카렌다사](http://www.bosungcalendar.com/bs/shop/index.php))을 분석하여 최신 **Python (FastAPI) + Neon DB (Serverless PostgreSQL) + Tailwind CSS** 기반으로 재구축한 모던 B2B/B2C 캘린더 제작 쇼핑몰 프로젝트입니다.

---

## 📁 프로젝트 폴더 및 파일 구조

```text
WEB_PROJECT/
├── .env                         # Neon DB 접속 정보 및 환경 변수 설정 (보안 파일, Git 제외)
├── .gitignore                   # Git 커밋 제외 목록 (.env, 캐시 등)
├── requirements.txt             # Python 의존성 라이브러리 목록
├── README.md                    # 프로젝트 전체 문서 및 가이드
├── run.py                       # 로컬 개발 서버 실행 스크립트 (FastAPI/Uvicorn)
│
├── app/                         # 웹 애플리케이션 핵심 패키지
│   ├── __init__.py
│   ├── main.py                  # FastAPI 앱 진입점, 수명주기(Lifespan), 미들웨어 설정
│   │
│   ├── core/                    # 설정 및 환경 상수
│   │   ├── __init__.py
│   │   └── config.py            # 앱 환경변수 로더 및 사업자/고객센터 정보
│   │
│   ├── db/                      # 데이터베이스 레이어
│   │   ├── __init__.py
│   │   ├── connection.py        # Neon DB 커넥션 풀 (ThreadedConnectionPool) & 컨텍스트 매니저
│   │   └── queries.py           # 상품, 카테고리, 견적문의, 게시판 SQL 쿼리 모듈
│   │
│   ├── routes/                  # 라우트 핸들러 (컨트롤러)
│   │   ├── __init__.py
│   │   ├── pages.py             # 웹 페이지 뷰 라우트 (홈, 카테고리, 상세, 견적, 공지, FAQ, Q&A, 회사소개)
│   │   └── api.py               # RESTful API 엔드포인트 (AJAX 견적 접수, 검색 등)
│   │
│   ├── static/                  # 정적 리소스 파일
│   │   ├── css/
│   │   │   └── style.css        # Pretendard 웹폰트 및 커스텀 스크롤바 스타일
│   │   └── js/
│   │       └── main.js          # 모바일 네비게이션 드로어 및 클라이언트 인터랙션
│   │
│   └── templates/               # Jinja2 반응형 HTML 템플릿
│       ├── base.html            # 공통 레이아웃 (헤더, 네비게이션, 모바일 메뉴, 푸터)
│       ├── index.html           # 메인 홈 화면 (히어로 배너, 추천 카렌다 그리드, 공지사항)
│       ├── company.html         # 회사 소개 및 오시는 길
│       ├── boards/              # [신규] 게시판 템플릿 모음
│       │   ├── notice_list.html # 공지사항 목록
│       │   ├── notice_detail.html# 공지사항 상세 본문
│       │   ├── faq.html         # 자주 묻는 질문 (FAQ 아코디언 UI)
│       │   ├── qna_list.html    # 질문과 답변 (Q&A 목록)
│       │   ├── qna_form.html    # 1:1 질문 작성 폼 (비밀글 보호)
│       │   └── qna_detail.html  # 질문 및 관리자 답변 확인
│       ├── products/
│       │   ├── list.html        # 카테고리별 상품 목록 (정렬, 필터링, 페이징)
│       │   ├── detail.html      # 상품 상세 페이지 (1월~12월 월별 내지 인터랙티브 뷰어)
│       │   └── search.html      # 상품 통합 검색 결과 화면
│       └── quotes/
│           ├── form.html        # 온라인 견적 및 주문 문의 접수 폼 (선택 상품 자동 연동)
│           └── list.html        # 견적 및 주문 문의 게시판 목록
│
└── scripts/                     # 유틸리티 및 데이터 관리 스크립트
    ├── create_tables.py         # Neon DB 핵심 테이블 스키마 초기화 및 카테고리 시딩
    ├── create_board_tables.py   # FAQ 및 Q&A 게시판 테이블 생성 & 데이터 시딩
    ├── create_admin_tables.py   # [신규] admins 테이블 생성 및 기본 관리자 계정 시딩
    ├── import_sample_products.py# 실제 사이트 크롤링 및 샘플 상품/이미지 적재
    └── test_db.py               # Neon DB 연결 테스트 스크립트
```

---

## 🛠️ 주요 기능

1. **14개 달력 카테고리 체계 완벽 구축**
   - 대형카렌다, 국내풍경, 세계풍경, 숫자판, 탁상용, 일력 등 분류별 탐색 지원
2. **달력 인쇄 전문 사양 표시 및 월별 내지 뷰어**
   - 규격, 매수, 지질/용지, 제본방식, 상호 인쇄란 크기 안내
   - **표지 및 1월부터 12월까지의 월별 내지 고해상도 이미지 실시간 전환 미리보기**
3. **B2B 온라인 견적 접수 시스템**
   - 선택한 달력 상품의 정보가 자동으로 연동되는 간편 견적 신청
   - 인쇄 상호 문구 및 로고 시안 접수, 예상 주문 수량별 견적 요청
4. **고객 소통 게시판 3종 완비**
   - 공지사항 (Notice), 자주 묻는 질문 (FAQ 아코디언), 1:1 질문과 답변 (Q&A 비밀글)
5. **[신규] 관리자 센터 (Admin Center)**
   - **보안 세션 로그인 인증** (`/admin/login`)
   - **대시보드 통계**: 총 상품 수, 대기 중 견적, 미답변 질문 요약
   - **상품 및 가격 관리**: 가격 실시간 인라인 수정, 상세 정보/이미지 수정, 신규 상품 등록
   - **고객 질문 답변 작성**: 미답변 질문에 관리자 답변 등록 시 '답변완료' 자동 반영
   - **견적 문의 상태 관리**: 접수된 견적 확인, 상태 변경(상담중/완료), 관리자 메모
   - **공지사항 등록/삭제 관리**
6. **Neon PostgreSQL 최적화**
   - 커넥션 풀링(`ThreadedConnectionPool`) 적용으로 안정적인 다중 요청 처리

---

## 🚀 실행 방법

### 1. 패키지 설치
```bash
python3 -m pip install -r requirements.txt
```

### 2. 로컬 웹 서버 실행
```bash
python3 run.py
```

* **쇼핑몰 메인**: `http://127.0.0.1:8000`
* **관리자 센터**: `http://127.0.0.1:8000/admin`
  * 기본 아이디: `admin`
  * 기본 비밀번호: `admin1234`

