"""중소벤처기업부(MSS) 사업공고 수집기

중소벤처기업부: 스타트업/중소기업 정책 총괄 부처
- URL: https://www.mss.go.kr
- 사업공고 페이지 크롤링
"""
import re
import logging
from typing import List

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.database import Database

logger = logging.getLogger(__name__)

MSS_LIST_URL = "https://www.mss.go.kr/site/smba/ex/bbs/List.do"
MSS_BASE_URL = "https://www.mss.go.kr"


class MssCollector(BaseCollector):
    """중소벤처기업부 사업공고 크롤링 수집기"""

    SOURCE_NAME = "mss"

    def collect(self) -> List[dict]:
        logger.info("중소벤처기업부 크롤링 수집 시작")
        postings = []

        try:
            params = {"cbIdx": 310, "pageIndex": 1}
            response = self._request(MSS_LIST_URL, params=params)
            if response.encoding and response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            rows = soup.select("table tbody tr")
            if not rows:
                rows = soup.select("ul.board-list li")

            for row in rows:
                link = row.find("a", href=True)
                if not link:
                    continue

                title = link.text.strip()
                href = link.get("href", "")

                if not title or len(title) < 5:
                    continue

                url = href if href.startswith("http") else MSS_BASE_URL + href

                # 날짜 추출
                dates = re.findall(r"(\d{4}[.\-]\d{2}[.\-]\d{2})", row.text)
                start_date = self._normalize_date(dates[0]) if len(dates) >= 1 else ""
                end_date = self._normalize_date(dates[1]) if len(dates) >= 2 else ""

                postings.append({
                    "id": Database.generate_id(title, url),
                    "title": title,
                    "organization": "중소벤처기업부",
                    "category": "",
                    "start_date": start_date,
                    "end_date": end_date,
                    "target": "",
                    "url": url,
                    "summary": "",
                    "source": self.SOURCE_NAME,
                })

        except Exception as e:
            logger.error(f"중소벤처기업부 크롤링 실패: {e}")

        # 중복 제거
        seen = set()
        unique = []
        for p in postings:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique.append(p)

        logger.info(f"중소벤처기업부 수집 완료: {len(unique)}건")
        return unique
