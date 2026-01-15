import os
from fastmcp import FastMCP
import requests

mcp = FastMCP("lost-article-mcp")

API_KEY = os.getenv("SEOUL_API_KEY")
SERVICE = "lostArticleInfo"

if not API_KEY:
    raise RuntimeError("SEOUL_API_KEY 환경변수가 설정되지 않았습니다.")

def get_list_total_count():
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/{SERVICE}/1/1"
    data = requests.get(url, timeout=5).json()
    return data[SERVICE]["list_total_count"]


@mcp.tool(
    name="latest_detail",
    description="서울시 분실물 최신 정보 조회"
)
def latest_detail(item: str, start_date: str):
    """
    item은 사용자의 자연어 입력을 아래 고정 카테고리 중 하나로 반드시 변환한 값이어야 한다.

    [사용 가능한 카테고리]
    - 지갑
    - 쇼핑백
    - 서류봉투
    - 가방
    - 배낭
    - 핸드폰
    - 옷
    - 책
    - 파일
    - 장난감
    - 기타

    [매핑 규칙]
    1. 사용자가 입력한 단어의 의미를 우선적으로 해석한다.
    2. 아래 예시와 같이 동의어·유사어는 동일 카테고리로 통합한다.

    - 핸드폰: 휴대폰, 스마트폰, 갤럭시, 아이폰, 아이폰15, 폴드폰, 플립폰 등
    - 가방: 숄더백, 크로스백, 토트백, 핸드백 등
    - 배낭: 백팩, 책가방, 등산가방 등
    - 지갑: 카드지갑, 반지갑, 장지갑 등
    - 옷: 상의, 하의, 외투, 패딩, 코트, 바지, 티셔츠 등
    - 책: 교재, 전공서적, 문제집, 노트 등
    - 파일: 서류철, 바인더, 클리어파일 등
    - 쇼핑백: 종이가방, 브랜드백 등
    - 장난감: 인형, 피규어, 완구 등

    3. 복수 후보가 있을 경우 가장 대표적인 하나만 선택한다.
    4. 어떤 카테고리에도 명확히 속하지 않으면 반드시 '기타'를 사용한다.
    5. 최종적으로 item에는 위 카테고리 문자열 중 하나만 출력한다.
    item: ['지갑', '쇼핑백', '서류봉투', '가방', '배낭', '핸드폰', '옷', '책', '파일', '장난감'] 중 한 카테고리 (이에 해당하지 않으면 '기타')
    start_date: YYYYMMDD 형식
    """

    if not item or not start_date:
        return {
            "error": "item and start_date are required"
        }

    total = get_list_total_count()
    end = total
    start = max(1, end - 999)

    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/{SERVICE}/{start}/{end}"
    data = requests.get(url, timeout=5).json()
    rows = data[SERVICE].get("row", [])

    # 최신순 정렬
    rows.sort(key=lambda x: x.get("REG_YMD", ""), reverse=True)

    result = []
    for row in rows:
        reg_ymd = row.get("REG_YMD", "")
        lost_stts = row.get("LOST_STTS", "")
        lost_knd = row.get("LOST_KND", "")
        lost_nm = row.get("LOST_NM", "")
        detail = row.get("LGS_DTL_CN", "")

        # 1. LOST_NM에 '수령' 포함 시 제외
        if any(word in lost_nm for word in ("수령", "연락됨")):
            continue

        # 2. 조건 필터
        if (
            reg_ymd >= start_date
            and lost_stts not in ("수령", "연락됨")
            and lost_knd == item
        ):
            result.append({
                "LOST_NM": lost_nm,
                "LOST_STTS": lost_stts,
                "LGS_DTL_CN": detail
            })

    return {
        "count": len(result),
        "items": result
    }


if __name__ == "__main__":
    mcp.run()
