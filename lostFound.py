from fastmcp import FastMCP
import requests

mcp = FastMCP("lost-article-mcp")

API_KEY = "6551505547616e6438396e75595a42"
SERVICE = "lostArticleInfo"


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
    item: 찾는 물건 (지갑, 쇼핑백, 서류봉투, 가방, 배낭, 핸드폰, 옷, 책, 파일, 장난감, 기타)
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
