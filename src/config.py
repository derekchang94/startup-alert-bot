"""설정 관리 모듈"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 기준 .env 로드
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")


class Config:
    # Slack
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "series_a")

    # API Keys (공공데이터포털 data.go.kr)
    BIZINFO_API_KEY = os.getenv("BIZINFO_API_KEY", "")
    SMES_API_KEY = os.getenv("SMES_API_KEY", "")
    KSTARTUP_API_KEY = os.getenv("KSTARTUP_API_KEY", "")

    # Database
    DB_PATH = os.getenv("DB_PATH", str(_project_root / "data" / "postings.db"))

    # Collection
    COLLECT_COUNT = int(os.getenv("COLLECT_COUNT", "50"))
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))

    # Filters
    FILTER_CATEGORIES = [
        c.strip() for c in os.getenv("FILTER_CATEGORIES", "").split(",") if c.strip()
    ]
    FILTER_KEYWORDS = [
        k.strip() for k in os.getenv("FILTER_KEYWORDS", "").split(",") if k.strip()
    ]
