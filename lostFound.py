from dotenv import load_dotenv
from fastmcp import FastMCP
import requests
import os

mcp = FastMCP("lostfound-mcp")

# load API
load_dotenv() 
API_KEY = os.getenv("SEOUL_API_KEY") 
SERVICE = "lostArticleInfo"

@mcp.tool
def search_lost_item(
    item: str,
    start_date: str,
    end_date: str
    ) -> list:
    """
    기간 내 특정 분실물 검색

    - item: 찾는 물건 (ex: 지갑, 에어팟)
    - start_date: YYYYMMDD
    - end_date: YYYYMMDD
    """
    results = []
    start = 1
    step = 100  # 페이지 단위

    while True:
        end = start + step - 1
        url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/{SERVICE}/{start}/{end}"

        try:
            response = requests.get(url, timeout=5)
            data = response.json()
        except Exception:
            break

        # 서비스 키가 없으면 중단
        if SERVICE not in data:
            break

        rows = data[SERVICE].get("row", [])
        if not rows:
            break

        for row in rows:
            get_date = row.get("GET_YMD", "")
            lost_article = row.get("LOST_NM", "")

            if (
                start_date <= get_date <= end_date
                and item in lost_article
            ):
                results.append(row)

        start += step

    return results
     

@mcp.tool
def api_health_check() -> str:
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/lostArticleInfo/1/1"
    res = requests.get(url)
    return res.json()["lostArticleInfo"]["RESULT"]["CODE"]

if __name__ == "__main__":
    mcp.run(transport="http")