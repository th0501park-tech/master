import io
import csv
from typing import List, Dict, Any, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.db import queries


def _get_category_maps(categories: List[Dict[str, Any]]) -> Tuple[Dict[str, int], Dict[int, str]]:
    """카테고리 이름 -> ID, ID -> 이름 매핑 딕셔너리 생성"""
    name_to_id = {}
    id_to_name = {}
    for cat in categories:
        cid = cat["id"]
        cname = cat["name"].strip()
        name_to_id[cname] = cid
        name_to_id[cname.replace(" ", "")] = cid
        id_to_name[cid] = cname
    return name_to_id, id_to_name


def generate_product_template_excel(categories: List[Dict[str, Any]]) -> bytes:
    """
    관리자 상품 일괄 등록용 표준 엑셀 양식 생성 (.xlsx)
    - Sheet 1: 상품등록양식 (헤더 및 예시 데이터 포함)
    - Sheet 2: 카테고리_참조목록 (작성 시 카테고리명 참고용)
    """
    wb = openpyxl.Workbook()
    
    # ------------------ Sheet 1: 상품등록양식 ------------------
    ws1 = wb.active
    ws1.title = "상품일괄등록양식"
    ws1.views.sheetView[0].showGridLines = True

    # 스타일 정의
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # 네이비 블루
    header_font = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
    
    sample_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")  # 연한 회색 배경
    sample_font = Font(name="맑은 고딕", size=10, color="475569")
    
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )
    
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    headers = [
        "카테고리(필수)",
        "상품코드(필수)",
        "상품명(필수)",
        "단가(필수/원)",
        "규격",
        "매수",
        "용지/지질",
        "제본",
        "인쇄란규격",
        "최소주문수량",
        "대표이미지URL",
        "상세설명"
    ]

    ws1.append(headers)
    ws1.row_dimensions[1].height = 28

    for col_idx, _ in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = thin_border

    # 샘플 예시 행 2개 추가
    first_cat = categories[0]["name"] if categories else "대형카렌다"
    second_cat = categories[9]["name"] if len(categories) > 9 else (categories[1]["name"] if len(categories) > 1 else first_cat)

    sample_rows = [
        [
            first_cat,
            "EX-SAMPLE01",
            "[예시] 2027 명품 한국의 산하 벽걸이 달력",
            8500,
            "1,000mm X 700mm",
            "13매",
            "고급 스노우지 150g",
            "P.V.C 홀더",
            "180mm X 50mm",
            100,
            "",
            "사계절 명산의 풍경을 담은 보성문화 최고급 대형 벽걸이 캘린더"
        ],
        [
            second_cat,
            "EX-SAMPLE02",
            "[예시] 2027 심플 모던 탁상용 캘린더",
            4800,
            "250mm X 180mm",
            "14매",
            "랑데뷰 210g",
            "트윈링 스프링",
            "230mm X 30mm",
            100,
            "",
            "책상 위 편리한 일정 관리를 위한 모던 탁상 달력 (음력 및 절기 표기)"
        ]
    ]

    for row_idx, row_data in enumerate(sample_rows, 2):
        ws1.append(row_data)
        ws1.row_dimensions[row_idx].height = 24
        for col_idx, val in enumerate(row_data, 1):
            cell = ws1.cell(row=row_idx, column=col_idx)
            cell.fill = sample_fill
            cell.font = sample_font
            cell.border = thin_border
            if col_idx in [1, 2, 6, 8, 10]:
                cell.alignment = align_center
            elif col_idx == 4:
                cell.alignment = align_right
                cell.number_format = "#,##0"
            else:
                cell.alignment = align_left

    # 열 너비 설정
    col_widths = {
        1: 20,  # 카테고리
        2: 16,  # 상품코드
        3: 36,  # 상품명
        4: 15,  # 단가
        5: 22,  # 규격
        6: 12,  # 매수
        7: 22,  # 용지
        8: 16,  # 제본
        9: 18,  # 인쇄란
        10: 14, # 최소수량
        11: 28, # 이미지URL
        12: 45  # 상세설명
    }
    for col_idx, width in col_widths.items():
        ws1.column_dimensions[get_column_letter(col_idx)].width = width

    # ------------------ Sheet 2: 카테고리_참조목록 ------------------
    ws2 = wb.create_sheet(title="카테고리_참조목록")
    ws2.views.sheetView[0].showGridLines = True
    
    cat_header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    cat_headers = ["카테고리 ID", "카테고리명 (양식 입력값)", "영문 식별자(Slug)"]
    ws2.append(cat_headers)
    ws2.row_dimensions[1].height = 26

    for col_idx, _ in enumerate(cat_headers, 1):
        cell = ws2.cell(row=1, column=col_idx)
        cell.fill = cat_header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = thin_border

    for row_idx, cat in enumerate(categories, 2):
        ws2.append([cat["id"], cat["name"], cat.get("slug", "")])
        ws2.row_dimensions[row_idx].height = 22
        for col_idx in range(1, 4):
            cell = ws2.cell(row=row_idx, column=col_idx)
            cell.font = Font(name="맑은 고딕", size=10)
            cell.border = thin_border
            if col_idx in [1, 3]:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

    ws2.column_dimensions["A"].width = 16
    ws2.column_dimensions["B"].width = 30
    ws2.column_dimensions["C"].width = 25

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def generate_products_export_excel(products: List[Dict[str, Any]], categories: List[Dict[str, Any]]) -> bytes:
    """
    현재 상품 목록을 엑셀로 내보내기 (.xlsx)
    수정 후 다시 업로드할 수 있도록 양식과 동일한 구조 제공
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "등록상품목록"
    ws.views.sheetView[0].showGridLines = True

    header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")  # 딥 틸/에메랄드
    header_font = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    headers = [
        "상품ID",
        "카테고리",
        "상품코드",
        "상품명",
        "단가(원)",
        "규격",
        "매수",
        "용지/지질",
        "제본",
        "인쇄란규격",
        "최소주문수량",
        "대표이미지URL",
        "상세설명"
    ]
    ws.append(headers)
    ws.row_dimensions[1].height = 28

    for col_idx, _ in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = thin_border

    for row_idx, p in enumerate(products, 2):
        row_data = [
            p.get("id"),
            p.get("category_name") or "",
            p.get("item_code") or "",
            p.get("name") or "",
            p.get("price") or 0,
            p.get("dimensions") or "",
            p.get("sheets") or "",
            p.get("paper_type") or "",
            p.get("binding") or "",
            p.get("imprint_size") or "",
            p.get("min_quantity") or 100,
            p.get("thumbnail_url") or "",
            p.get("description") or ""
        ]
        ws.append(row_data)
        ws.row_dimensions[row_idx].height = 22
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = Font(name="맑은 고딕", size=10)
            cell.border = thin_border
            if col_idx in [1, 2, 3, 7, 9, 11]:
                cell.alignment = align_center
            elif col_idx == 5:
                cell.alignment = align_right
                cell.number_format = "#,##0"
            else:
                cell.alignment = align_left

    col_widths = {
        1: 10, 2: 18, 3: 16, 4: 35, 5: 14, 6: 22, 7: 12,
        8: 20, 9: 16, 10: 18, 11: 14, 12: 28, 13: 40
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # 카테고리 참조 시트
    ws2 = wb.create_sheet(title="카테고리_참조목록")
    ws2.views.sheetView[0].showGridLines = True
    cat_headers = ["카테고리 ID", "카테고리명", "영문 식별자"]
    ws2.append(cat_headers)
    for row_idx, cat in enumerate(categories, 2):
        ws2.append([cat["id"], cat["name"], cat.get("slug", "")])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _normalize_header(header: str) -> str:
    """헤더 문자열 정규화 (괄호, 공백 등 제거)"""
    if not header:
        return ""
    h = str(header).strip().lower()
    for char in [" ", "(필수)", "(원)", "(필수/원)", "원", "(", ")", "_", "-", "/"]:
        h = h.replace(char, "")
    return h


def parse_and_import_products(
    file_bytes: bytes,
    filename: str,
    update_existing: bool = True
) -> Dict[str, Any]:
    """
    엑셀(.xlsx) 또는 CSV 파일을 읽어 상품 일괄 등록/수정 수행
    """
    categories = queries.get_categories()
    name_to_id, id_to_name = _get_category_maps(categories)
    default_category_id = categories[0]["id"] if categories else 1

    rows_data: List[List[Any]] = []
    
    # 1. 파일 파싱 (.csv vs .xlsx)
    is_csv = filename.lower().endswith(".csv")
    if is_csv:
        # 인코딩 시도 (utf-8-sig, cp949, euc-kr)
        content_str = None
        for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
            try:
                content_str = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if content_str is None:
            return {
                "success": False,
                "message": "CSV 파일의 인코딩을 인식할 수 없습니다. UTF-8 또는 엑셀(.xlsx) 형식을 사용해주세요.",
                "total": 0, "created": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []
            }
        reader = csv.reader(io.StringIO(content_str))
        rows_data = [row for row in reader if any(cell.strip() for cell in row)]
    else:
        # Excel .xlsx 파싱
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            # 첫 번째 시트 또는 상품일괄등록양식 시트 선택
            sheet_name = "상품일괄등록양식" if "상품일괄등록양식" in wb.sheetnames else wb.sheetnames[0]
            ws = wb[sheet_name]
            for row in ws.iter_rows(values_only=True):
                # 완전히 빈 행 제외
                if row and any(v is not None and str(v).strip() != "" for v in row):
                    rows_data.append([str(v).strip() if v is not None else "" for v in row])
        except Exception as e:
            return {
                "success": False,
                "message": f"엑셀 파일을 열 수 없습니다: {str(e)}",
                "total": 0, "created": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []
            }

    if not rows_data or len(rows_data) < 2:
        return {
            "success": False,
            "message": "업로드된 파일에 등록할 데이터 행이 없습니다.",
            "total": 0, "created": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []
        }

    # 2. 헤더 컬럼 매핑
    raw_headers = rows_data[0]
    header_indices = {}
    for idx, h in enumerate(raw_headers):
        norm = _normalize_header(h)
        if any(k in norm for k in ["카테고리", "분류", "category"]):
            header_indices["category"] = idx
        elif any(k in norm for k in ["상품코드", "코드", "itemcode", "품번"]):
            header_indices["item_code"] = idx
        elif any(k in norm for k in ["상품명", "제품명", "name", "제목"]):
            header_indices["name"] = idx
        elif any(k in norm for k in ["단가", "가격", "판매가", "price"]):
            header_indices["price"] = idx
        elif any(k in norm for k in ["규격", "사이즈", "dimensions"]):
            header_indices["dimensions"] = idx
        elif any(k in norm for k in ["매수", "페이지", "sheets"]):
            header_indices["sheets"] = idx
        elif any(k in norm for k in ["용지", "지질", "papertype"]):
            header_indices["paper_type"] = idx
        elif any(k in norm for k in ["제본", "binding"]):
            header_indices["binding"] = idx
        elif any(k in norm for k in ["인쇄란", "인쇄규격", "imprint"]):
            header_indices["imprint_size"] = idx
        elif any(k in norm for k in ["최소수량", "최소주문수량", "minquantity"]):
            header_indices["min_quantity"] = idx
        elif any(k in norm for k in ["대표이미지", "이미지url", "썸네일", "thumbnail"]):
            header_indices["thumbnail_url"] = idx
        elif any(k in norm for k in ["상세설명", "설명", "description"]):
            header_indices["description"] = idx

    # 필수 컬럼 체크
    if "item_code" not in header_indices or "name" not in header_indices:
        return {
            "success": False,
            "message": "필수 헤더인 '상품코드'와 '상품명' 컬럼을 찾을 수 없습니다. 양식을 확인해주세요.",
            "total": 0, "created": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []
        }

    def get_val(row: list, key: str, default: str = "") -> str:
        idx = header_indices.get(key)
        if idx is not None and idx < len(row):
            val = str(row[idx]).strip()
            return val if val is not None else default
        return default

    # 3. 행별 처리
    created_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    errors: List[str] = []

    for row_num, row in enumerate(rows_data[1:], start=2):
        item_code = get_val(row, "item_code")
        name = get_val(row, "name")

        # 빈 행이면 건너뜀
        if not item_code and not name:
            continue

        # 예시 데이터 행 건너뛰기 ([예시] 또는 EX-SAMPLE)
        if item_code.startswith("EX-SAMPLE") or name.startswith("[예시]"):
            continue

        if not item_code:
            errors.append(f"{row_num}번째 행: 상품코드가 비어 있어 제외되었습니다.")
            failed_count += 1
            continue

        if not name:
            errors.append(f"{row_num}번째 행(코드: {item_code}): 상품명이 비어 있어 제외되었습니다.")
            failed_count += 1
            continue

        # 가격 정수 변환
        raw_price = get_val(row, "price", "0")
        try:
            # 쉼표, 원, 공백 제거
            clean_price = "".join(filter(str.isdigit, raw_price))
            price = int(clean_price) if clean_price else 0
        except ValueError:
            price = 0

        # 최소주문수량 변환
        raw_min_qty = get_val(row, "min_quantity", "100")
        try:
            clean_min_qty = "".join(filter(str.isdigit, raw_min_qty))
            min_quantity = int(clean_min_qty) if clean_min_qty else 100
        except ValueError:
            min_quantity = 100

        # 카테고리 매핑
        raw_cat = get_val(row, "category")
        category_id = None
        if raw_cat:
            # 1) 숫자로 입력된 경우
            if raw_cat.isdigit() and int(raw_cat) in id_to_name:
                category_id = int(raw_cat)
            # 2) 카테고리명으로 입력된 경우
            elif raw_cat in name_to_id:
                category_id = name_to_id[raw_cat]
            elif raw_cat.replace(" ", "") in name_to_id:
                category_id = name_to_id[raw_cat.replace(" ", "")]
            else:
                # 부분 일치 검색 시도
                for cname, cid in name_to_id.items():
                    if raw_cat in cname or cname in raw_cat:
                        category_id = cid
                        break

        if not category_id:
            category_id = default_category_id

        product_data = {
            "category_id": category_id,
            "item_code": item_code,
            "name": name,
            "price": price,
            "dimensions": get_val(row, "dimensions"),
            "sheets": get_val(row, "sheets"),
            "paper_type": get_val(row, "paper_type"),
            "binding": get_val(row, "binding"),
            "imprint_size": get_val(row, "imprint_size"),
            "min_quantity": min_quantity,
            "description": get_val(row, "description"),
            "thumbnail_url": get_val(row, "thumbnail_url"),
        }

        try:
            action = queries.upsert_product_excel(product_data, update_existing=update_existing)
            if action == "created":
                created_count += 1
            elif action == "updated":
                updated_count += 1
            elif action == "skipped":
                skipped_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(f"{row_num}번째 행(코드: {item_code}): DB 저장 오류 - {str(e)}")

    total_processed = created_count + updated_count + skipped_count + failed_count
    return {
        "success": True,
        "message": f"엑셀 처리 완료: 신규 등록 {created_count}건, 정보 수정 {updated_count}건, 건너뜀 {skipped_count}건, 실패 {failed_count}건",
        "total": total_processed,
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "errors": errors
    }
