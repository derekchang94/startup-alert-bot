"""메인 실행 스크립트 - 수집 + Slack 알림 오케스트레이션

실행 정책:
- 하루 1회 오전 11시 실행 (외부 cron 트리거)
- 이번 실행에서 신규 수집된 공고만 필터링하여 Slack 발송
- 이미 DB에 존재하는 공고는 무시 (중복 발송 방지)
- 같은 날 이미 발송했으면 재발송하지 않음
"""
import sys
import logging
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

from src.config import Config
from src.database import Database
from src.collectors.bizinfo import BizinfoCollector
from src.collectors.smes import SmesCollector
from src.collectors.kstartup import KStartupCollector
from src.collectors.tips import TipsCollector
from src.collectors.tipa import TipaCollector
from src.collectors.nipa import NipaCollector
from src.collectors.thevc import TheVCCollector
from src.collectors.mss import MssCollector
from src.notifier import SlackNotifier
from src.filters import filter_relevant_postings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def collect_postings(db: Database) -> list:
    """모든 수집기를 실행하고 신규 공고 목록(dict 리스트) 반환

    DB에 이미 존재하는 공고는 insert_posting()에서 걸러지므로,
    반환되는 리스트는 이번 실행에서 처음 발견된 공고만 포함.
    """
    collectors = []

    # 웹 크롤링 수집기 (API 키 불필요)
    collectors.append(BizinfoCollector())
    collectors.append(TipsCollector())
    collectors.append(TipaCollector())
    collectors.append(NipaCollector())
    collectors.append(TheVCCollector())
    collectors.append(MssCollector())

    if Config.SMES_API_KEY:
        collectors.append(SmesCollector())
    else:
        logger.warning("SMES_API_KEY 미설정 - 중소벤처24 수집 건너뜀")

    if Config.KSTARTUP_API_KEY:
        collectors.append(KStartupCollector())
    else:
        logger.warning("KSTARTUP_API_KEY 미설정 - K-Startup 수집 건너뜀")

    if not collectors:
        logger.error("활성화된 수집기가 없습니다. API 키를 설정해주세요.")
        return []

    new_postings = []
    for collector in collectors:
        try:
            postings = collector.collect()
            for posting in postings:
                if db.insert_posting(posting):
                    new_postings.append(posting)
        except Exception as e:
            logger.error(f"{collector.__class__.__name__} 실행 실패: {e}")

    return new_postings


def main():
    logger.info("=" * 50)
    logger.info("스타트업 지원사업 공고 수집 시작")
    logger.info("=" * 50)

    if not Config.SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        sys.exit(1)

    db = Database()
    try:
        # 0. 오늘 이미 알림을 보냈는지 확인 → 중복 발송 방지
        today = datetime.now().strftime("%Y-%m-%d")
        if db.has_sent_today(today):
            logger.info(f"{today} 알림 이미 발송 완료 - 중복 발송 방지로 종료")
            return

        # 1. 공고 수집 (DB 기준 신규 공고만 반환)
        new_postings = collect_postings(db)
        logger.info(f"신규 수집: {len(new_postings)}건")

        # 2. 필터링 (만료/과거 배제 → 키워드 매칭 → 지역 제한 배제)
        filtered = filter_relevant_postings(new_postings)
        logger.info(f"필터링 후 발송 대상: {len(filtered)}건")

        # 3. Slack 알림 발송
        notifier = SlackNotifier()
        success = notifier.send_daily_report(filtered)

        if success:
            # 오늘 발송 기록 (중복 발송 방지)
            db.record_daily_send(today, len(filtered))
            # 신규 수집된 모든 공고를 알림 처리 (필터에서 탈락한 것 포함)
            # → 다음 실행에서 재처리되지 않도록
            if new_postings:
                db.mark_as_notified([p["id"] for p in new_postings])
            logger.info(f"알림 발송 완료 (발송 {len(filtered)}건 / 수집 {len(new_postings)}건)")
        else:
            logger.warning("Slack 알림 전송에 문제가 발생했습니다.")
            sys.exit(1)

        # 4. 통계 출력
        stats = db.get_stats()
        logger.info(f"DB 통계 - 전체: {stats['total']}, 알림완료: {stats['notified']}, 대기: {stats['pending']}")
        for source, cnt in stats["by_source"].items():
            logger.info(f"  {source}: {cnt}건")

        logger.info("모든 작업 완료")

    except Exception as e:
        logger.error(f"실행 중 오류: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
