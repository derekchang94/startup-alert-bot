"""THE VC 지원사업 탐색 수집기

THE VC: 한국 스타트업 투자 데이터베이스
- URL: https://thevc.kr/grants
- 정부/민간 지원사업 공고 통합 제공
"""
import re
import logging
from typing import List

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.database import Database

logger = logging.getLogger(__name__)

THEVC_GRANTS_URL = "https://thevc.kr/grants"
THEVC_BASE_URL = "https://thevc.kr"


class TheVCCollector(BaseCollector):
    """THE VC 지원사업 크롤링 수집기"""

    SOURCE_NAME = "thevc"

    def collect(self) -> List[dict]:
        logger.info("THE VC 크롤링 수집 시작")
        postings = []

        try:
            response = self._request(THEVC_GRANTS_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            # 공고 카드/리스트 항목 추출
            items = soup.select("a[href*='/grants/']")
            if not items:
                items = soup.find_all("a", href=re.compile(r"/grants/\d+|/program"))

            for item in items:
                title = item.text.strip()
                href = item.get("href", "")

                if not title or len(title) < 5:
                    continue

                url = href if href.startswith("http") else THEVC_BASE_URL + href

                # 부모 요소에서 추가 정보 추출
                parent = item.parent
                parent_text = parent.text if parent else ""

                # D-day, 기관명 등 추출 시도
                org = ""
                d_day = ""
                org_match = re.search(r"([\w가-힣]+(?:부|원|청|진흥원|재단))", parent_text)
                if org_match:
                    org = org_match.group(1)
                d_match = re.search(r"D-(\d+)", parent_text)
                if d_match:
                    d_day = f"D-{d_match.group(1)}"

                postings.append({
                    "id": Database.generate_id(title, url),
                    "title": title,
                    "organization": org,
                    "category": "",
                    "start_date": "",
                    "end_date": d_day,
                    "target": "",
                    "url": url,
                    "summary": "",
                    "source": self.SOURCE_NAME,
                })

        except Exception as e:
            logger.error(f"THE VC 크롤링 실패: {e}")

        # 중복 제거
        seen = set()
        unique = []
        for p in postings:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique.append(p)

        logger.info(f"THE VC 수집 완료: {len(unique)}건")
        return unique
