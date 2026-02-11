"""중소기업기술정보진흥원(TIPA) 공고 수집기

TIPA: R&D 및 스마트공장 지원 전문기관
- URL: https://www.tipa.or.kr
- 지원사업 공고, 조달공고
"""
import re
import logging
from typing import List

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.database import Database

logger = logging.getLogger(__name__)

TIPA_LIST_URL = "https://www.tipa.or.kr/s0201"
TIPA_BASE_URL = "https://www.tipa.or.kr"


class TipaCollector(BaseCollector):
    """TIPA 지원사업 공고 크롤링 수집기"""

    SOURCE_NAME = "tipa"

    def collect(self) -> List[dict]:
        logger.info("TIPA 크롤링 수집 시작")
        postings = []

        try:
            response = self._request(TIPA_LIST_URL)
            if response.encoding and response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # 게시판 목록에서 링크 추출
            rows = soup.select("table tbody tr")
            if not rows:
                rows = soup.find_all("a", href=True)

            for row in rows:
                link = row.find("a", href=True) if row.name == "tr" else row
                if not link:
                    continue

                title = link.text.strip()
                href = link.get("href", "")

                if not title or len(title) < 5:
                    continue
                if "tipa.or.kr" not in href and not href.startswith("/"):
                    continue

                url = href if href.startswith("http") else TIPA_BASE_URL + href

                # 날짜 추출 시도
                date_match = re.search(r"(\d{4}[.\-]\d{2}[.\-]\d{2})", row.text if row.name == "tr" else "")

                postings.append({
                    "id": Database.generate_id(title, url),
                    "title": title,
                    "organization": "중소기업기술정보진흥원(TIPA)",
                    "category": "R&D",
                    "start_date": "",
                    "end_date": self._normalize_date(date_match.group(1)) if date_match else "",
                    "target": "",
                    "url": url,
                    "summary": "",
                    "source": self.SOURCE_NAME,
                })

        except Exception as e:
            logger.error(f"TIPA 크롤링 실패: {e}")

        # 중복 제거
        seen = set()
        unique = []
        for p in postings:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique.append(p)

        logger.info(f"TIPA 수집 완료: {len(unique)}건")
        return unique
