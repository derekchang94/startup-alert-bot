"""메인 실행 스크립트 - 수집 + Slack 알림 오케스트레이션"""
import sys
import logging
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


def collect_postings(db: Database) -> int:
    """모든 수집기를 실행하고 신규 공고 수 반환"""
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
        return 0

    new_count = 0
    for collector in collectors:
        try:
            postings = collector.collect()
            for posting in postings:
                if db.insert_posting(posting):
                    new_count += 1
        except Exception as e:
            logger.error(f"{collector.__class__.__name__} 실행 실패: {e}")

    return new_count


def send_notifications(db: Database) -> bool:
    """미발송 공고 중 스타트업/해외진출 관련만 Slack으로 전송"""
    notifier = SlackNotifier()
    unnotified = db.get_unnotified_postings()
    logger.info(f"미발송 공고: {len(unnotified)}건")

    # 스타트업/해외진출 관련 공고만 필터링
    unnotified = filter_relevant_postings(unnotified)

    success = notifier.send_daily_report(unnotified)

    if success and unnotified:
        db.mark_as_notified([p["id"] for p in unnotified])
        logger.info(f"{len(unnotified)}건 알림 완료 처리")

    return success


def main():
    logger.info("=" * 50)
    logger.info("스타트업 지원사업 공고 수집 시작")
    logger.info("=" * 50)

    if not Config.SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        sys.exit(1)

    db = Database()
    try:
        # 1. 공고 수집
        new_count = collect_postings(db)
        logger.info(f"신규 수집: {new_count}건")

        # 2. Slack 알림
        success = send_notifications(db)

        # 3. 통계 출력
        stats = db.get_stats()
        logger.info(f"DB 통계 - 전체: {stats['total']}, 알림완료: {stats['notified']}, 대기: {stats['pending']}")
        for source, cnt in stats["by_source"].items():
            logger.info(f"  {source}: {cnt}건")

        if not success:
            logger.warning("Slack 알림 전송에 문제가 발생했습니다.")
            sys.exit(1)

        logger.info("모든 작업 완료")

    except Exception as e:
        logger.error(f"실행 중 오류: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
