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

@mcp.prompt
def ask_about_item(item: str) -> str:
    """Generates a user message asking for an item category"""
    return f"해당 {item}이 어느 카테고리에 포함되는지 선택해주세요: 지갑, 쇼핑백, 서류봉투, 가방, 배낭, 핸드폰, 옷, 책, 파일, 장난감, 기타"

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
