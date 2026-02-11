"""TIPS 프로그램 공고 수집기

TIPS: 민간투자 주도형 기술창업 지원 프로그램
- URL: https://www.jointips.or.kr
- 선정공고, 이벤트, 뉴스 등
"""
import re
import logging
from typing import List

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.database import Database

logger = logging.getLogger(__name__)

TIPS_LIST_URL = "https://www.jointips.or.kr/bbs/board.php"
TIPS_BASE_URL = "https://www.jointips.or.kr"


class TipsCollector(BaseCollector):
    """TIPS 공고 크롤링 수집기"""

    SOURCE_NAME = "tips"

    def collect(self) -> List[dict]:
        logger.info("TIPS 크롤링 수집 시작")
        postings = []

        for bo_table in ["notice", "news"]:
            try:
                params = {"bo_table": bo_table, "page": 1}
                response = self._request(TIPS_LIST_URL, params=params)
                if response.encoding and response.encoding.lower() == "iso-8859-1":
                    response.encoding = response.apparent_encoding

                soup = BeautifulSoup(response.text, "html.parser")
                links = soup.find_all("a", href=re.compile(r"wr_id=\d+"))

                for link in links:
                    title = link.text.strip()
                    href = link.get("href", "")
                    if not title or len(title) < 5:
                        continue

                    url = href if href.startswith("http") else TIPS_BASE_URL + href

                    postings.append({
                        "id": Database.generate_id(title, url),
                        "title": title,
                        "organization": "TIPS (창업진흥원)",
                        "category": "TIPS",
                        "start_date": "",
                        "end_date": "",
                        "target": "",
                        "url": url,
                        "summary": "",
                        "source": self.SOURCE_NAME,
                    })

            except Exception as e:
                logger.error(f"TIPS {bo_table} 크롤링 실패: {e}")

        # 중복 제거
        seen = set()
        unique = []
        for p in postings:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique.append(p)

        logger.info(f"TIPS 수집 완료: {len(unique)}건")
        return unique
