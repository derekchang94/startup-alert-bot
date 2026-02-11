"""K-Startup 창업지원포털 API 수집기

실제 API 필드명 (2026-02-11 확인):
  biz_pbanc_nm    : 공고명
  pbanc_ntrp_nm   : 수행기관 (창업진흥원 등)
  supt_biz_clsfc  : 지원사업 분류 (사업화, 멘토링·컨설팅·교육 등)
  pbanc_rcpt_bgng_dt : 접수 시작일 (YYYYMMDD)
  pbanc_rcpt_end_dt  : 접수 종료일 (YYYYMMDD)
  aply_trgt       : 신청대상 (예비창업자, 청소년 등)
  detl_pg_url     : 상세 페이지 URL
  pbanc_ctnt      : 공고 내용 요약
  supt_regin      : 지원 지역
  rcrt_prgs_yn    : 모집 진행 여부 (Y/N)
  pbanc_sn        : 공고 일련번호
"""
import logging
from typing import List

from src.config import Config
from src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

KSTARTUP_API_URL = (
    "https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01"
)


class KStartupCollector(BaseCollector):
    """K-Startup 창업지원사업 공고 수집기"""

    SOURCE_NAME = "kstartup"

    def collect(self) -> List[dict]:
        logger.info("K-Startup API 수집 시작")
        postings = []

        try:
            # 진행중인 공고만 수집 (최신순)
            params = {
                "serviceKey": Config.KSTARTUP_API_KEY,
                "page": 1,
                "perPage": Config.COLLECT_COUNT,
                "returnType": "JSON",
            }
            response = self._request(KSTARTUP_API_URL, params=params)
            data = response.json()

            total = data.get("totalCount", 0)
            items = data.get("data", [])
            if not isinstance(items, list):
                items = []

            logger.info(f"K-Startup API 응답: 전체 {total}건, 현재 페이지 {len(items)}건")

            for item in items:
                title = (item.get("biz_pbanc_nm") or "").strip()
                url = (item.get("detl_pg_url") or "").strip()
                if not title:
                    continue

                # 모집 진행 중인 공고만 필터
                if item.get("rcrt_prgs_yn") != "Y":
                    continue

                pbanc_sn = item.get("pbanc_sn", "")
                posting_id = f"kstartup_{pbanc_sn}" if pbanc_sn else f"kstartup_{hash(title + url)}"

                postings.append({
                    "id": posting_id,
                    "title": title,
                    "organization": (item.get("pbanc_ntrp_nm") or "").strip(),
                    "category": (item.get("supt_biz_clsfc") or "").strip(),
                    "start_date": self._normalize_date(
                        item.get("pbanc_rcpt_bgng_dt") or ""
                    ),
                    "end_date": self._normalize_date(
                        item.get("pbanc_rcpt_end_dt") or ""
                    ),
                    "target": (item.get("aply_trgt") or "").strip(),
                    "url": url,
                    "summary": (item.get("pbanc_ctnt") or "").strip()[:300],
                    "source": self.SOURCE_NAME,
                })

        except Exception as e:
            logger.error(f"K-Startup API 수집 실패: {e}")

        logger.info(f"K-Startup 수집 완료: {len(postings)}건")
        return postings
