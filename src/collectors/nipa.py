"""정보통신산업진흥원(NIPA) 공고 수집기

NIPA: ICT/SW 분야 스타트업 지원 전문기관
- URL: https://www.nipa.kr
- SaaS, GovTech, IT스타트업 지원사업
"""
import re
import logging
from typing import List

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.database import Database

logger = logging.getLogger(__name__)

NIPA_LIST_URL = "https://www.nipa.kr/home/2-2"
NIPA_BASE_URL = "https://www.nipa.kr"


class NipaCollector(BaseCollector):
    """NIPA 사업공고 크롤링 수집기"""

    SOURCE_NAME = "nipa"

    def collect(self) -> List[dict]:
        logger.info("NIPA 크롤링 수집 시작")
        postings = []

        try:
            response = self._request(NIPA_LIST_URL)
            if response.encoding and response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # 게시판 목록에서 공고 링크 추출
            rows = soup.select("table tbody tr")
            if not rows:
                # 대체: 리스트 형태
                rows = soup.select("ul.board-list li, div.list-item")

            for row in rows:
                link = row.find("a", href=True)
                if not link:
                    continue

                title = link.text.strip()
                href = link.get("href", "")

                if not title or len(title) < 5:
                    continue

                url = href if href.startswith("http") else NIPA_BASE_URL + href

                # 날짜 추출
                date_match = re.search(r"(\d{4}[.\-]\d{2}[.\-]\d{2})", row.text)

                postings.append({
                    "id": Database.generate_id(title, url),
                    "title": title,
                    "organization": "정보통신산업진흥원(NIPA)",
                    "category": "ICT/SW",
                    "start_date": "",
                    "end_date": self._normalize_date(date_match.group(1)) if date_match else "",
                    "target": "",
                    "url": url,
                    "summary": "",
                    "source": self.SOURCE_NAME,
                })

        except Exception as e:
            logger.error(f"NIPA 크롤링 실패: {e}")

        # 중복 제거
        seen = set()
        unique = []
        for p in postings:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique.append(p)

        logger.info(f"NIPA 수집 완료: {len(unique)}건")
        return unique
