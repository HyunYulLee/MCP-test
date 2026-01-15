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
    name="normalize_item",
    description="자연어 분실물 설명을 고정 카테고리로 분류"
)
def normalize_item(user_input: str) -> str:
    """
    당신은 분실물 분류기이다.
    사용자의 자연어 입력을 해석하여 반드시 아래 카테고리 중 하나만 출력해야 한다.

    [출력 가능 카테고리]
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

    [판단 기준]
    - 단어가 아닌 의미 기준으로 판단한다.
    - 브랜드명, 제품명, 구어체를 모두 고려한다.
    - 가장 일반적인 분실물 분류를 선택한다.
    - 애매하면 반드시 '기타'를 선택한다.

    [예시]
    - 아이폰, 갤럭시, 휴대폰 → 핸드폰
    - 백팩, 책가방 → 배낭
    - 크로스백 → 가방
    - 카드지갑 → 지갑

    [출력 규칙]
    - **카테고리 단어 하나만 출력**
    - 설명, 문장, 따옴표 금지
    """
    return user_input


@mcp.tool(
    name="latest_detail",
    description="서울시 분실물 최신 정보 조회 (normalize_item 결과만 사용)"
)
def latest_detail(item: str, start_date: str):
    """
    item: normalize_item 도구의 출력값 (고정 카테고리 중 하나)
    start_date: YYYYMMDD
    """

    if not item or not start_date:
        return {"error": "item and start_date are required"}

    total = get_list_total_count()
    end = total
    start = max(1, end - 999)

    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/{SERVICE}/{start}/{end}"
    data = requests.get(url, timeout=5).json()
    rows = data[SERVICE].get("row", [])

    rows.sort(key=lambda x: x.get("REG_YMD", ""), reverse=True)

    result = []
    for row in rows:
        if (
            row.get("REG_YMD", "") >= start_date
            and row.get("LOST_STTS", "") not in ("수령", "연락됨")
            and row.get("LOST_KND", "") == item
            and not any(w in row.get("LOST_NM", "") for w in ("수령", "연락됨"))
        ):
            result.append({
                "LOST_NM": row.get("LOST_NM", ""),
                "LOST_STTS": row.get("LOST_STTS", ""),
                "LGS_DTL_CN": row.get("LGS_DTL_CN", "")
            })

    return {
        "item": item,
        "count": len(result),
        "items": result
    }



if __name__ == "__main__":
    mcp.run()
