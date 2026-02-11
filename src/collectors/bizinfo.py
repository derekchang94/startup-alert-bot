"""기업마당(Bizinfo) 웹 크롤링 수집기

기업마당 API는 자체 인증키가 필요하며 data.go.kr 키로는 동작하지 않으므로,
지원사업 공고 목록 페이지를 HTML 크롤링하여 수집한다.

크롤링 대상: https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do
"""
import logging
import re
from typing import List

from bs4 import BeautifulSoup

from src.config import Config
from src.collectors.base import BaseCollector
from src.database import Database

logger = logging.getLogger(__name__)

BIZINFO_LIST_URL = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"
BIZINFO_BASE_URL = "https://www.bizinfo.go.kr"


class BizinfoCollector(BaseCollector):
    """기업마당 지원사업 공고 크롤링 수집기"""

    SOURCE_NAME = "bizinfo"

    def collect(self) -> List[dict]:
        logger.info("기업마당 크롤링 수집 시작")
        postings = []

        try:
            params = {
                "rows": min(Config.COLLECT_COUNT, 30),
                "cpage": 1,
            }
            response = self._request(BIZINFO_LIST_URL, params=params)

            if response.encoding and response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # 공고 목록 테이블에서 행 추출
            rows = soup.select("table tbody tr")
            if not rows:
                # 대체: a 태그에서 공고 링크 직접 추출
                rows = soup.find_all("a", href=re.compile(r"selectSIIA200Detail"))

            logger.info(f"기업마당 페이지에서 {len(rows)}개 항목 발견")

            for row in rows:
                posting = self._parse_row(row)
                if posting:
                    postings.append(posting)

        except Exception as e:
            logger.error(f"기업마당 크롤링 실패: {e}")

        logger.info(f"기업마당 수집 완료: {len(postings)}건")
        return postings

    def _parse_row(self, element) -> dict:
        """테이블 행 또는 a 태그에서 공고 정보 파싱"""
        try:
            # <tr> 행인 경우
            if element.name == "tr":
                tds = element.find_all("td")
                if len(tds) < 3:
                    return None

                link = element.find("a", href=True)
                if not link:
                    return None

                title = link.text.strip()
                href = link.get("href", "")
                if not title:
                    return None

                # 기관명, 시작일, 종료일 추출 (테이블 구조에 따라)
                org = tds[1].text.strip() if len(tds) > 1 else ""
                start_date = ""
                end_date = ""

                # 날짜 패턴 찾기 (YYYY.MM.DD 또는 YYYY-MM-DD)
                date_pattern = re.compile(r"(\d{4}[.\-/]\d{2}[.\-/]\d{2})")
                for td in tds:
                    dates = date_pattern.findall(td.text)
                    if len(dates) >= 2:
                        start_date = self._normalize_date(dates[0])
                        end_date = self._normalize_date(dates[1])
                    elif len(dates) == 1 and not end_date:
                        end_date = self._normalize_date(dates[0])

            # <a> 태그인 경우
            elif element.name == "a":
                title = element.text.strip()
                href = element.get("href", "")
                org = ""
                start_date = ""
                end_date = ""
            else:
                return None

            if not title:
                return None

            url = href if href.startswith("http") else BIZINFO_BASE_URL + href

            return {
                "id": Database.generate_id(title, url),
                "title": title,
                "organization": org,
                "category": "",
                "start_date": start_date,
                "end_date": end_date,
                "target": "",
                "url": url,
                "summary": "",
                "source": self.SOURCE_NAME,
            }

        except Exception as e:
            logger.debug(f"행 파싱 실패: {e}")
            return None
