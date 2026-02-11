"""Slack 알림 전송 모듈 (Bot API + 스레드 방식)

메인 메시지: 오늘의 요약 (신규 공고 N건)
스레드 댓글: 각 공고 상세 (1건 = 1댓글)
"""
import json
import logging
import time
from datetime import datetime
from typing import List, Optional

import requests

from src.config import Config

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack Bot API를 통한 스레드 기반 알림 전송"""

    def __init__(self):
        self.bot_token = Config.SLACK_BOT_TOKEN
        self.channel = Config.SLACK_CHANNEL
        self.api_url = "https://slack.com/api/chat.postMessage"
        self.headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def send_daily_report(self, postings: List[dict]) -> bool:
        """메인 메시지 + 스레드 댓글로 일일 리포트 전송"""
        if not postings:
            logger.info("신규 공고 없음 - 공고 없음 메시지 전송")
            return self._send_no_updates()

        # 1. 메인 메시지 전송 → thread_ts 확보
        today = datetime.now().strftime("%Y-%m-%d")

        # 소스별 건수 집계
        source_counts = {}
        for p in postings:
            src = p.get("source", "기타")
            source_counts[src] = source_counts.get(src, 0) + 1
        source_summary = " | ".join(f"{k}: {v}건" for k, v in source_counts.items())

        main_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"스타트업 지원사업 공고 알림 ({today})",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f":mega: *신규 스타트업/해외진출 관련 공고 {len(postings)}건*\n\n"
                        f":bar_chart: {source_summary}"
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": ":point_down: 각 공고 상세는 *스레드*에서 확인하세요.",
                    }
                ],
            },
        ]

        thread_ts = self._post_message(main_blocks, f"신규 스타트업 지원사업 공고 {len(postings)}건")
        if not thread_ts:
            return False

        # 2. 각 공고를 스레드 댓글로 전송
        for i, posting in enumerate(postings, 1):
            blocks = self._build_posting_blocks(posting, index=i, total=len(postings))
            self._post_message(blocks, posting["title"], thread_ts=thread_ts)
            time.sleep(0.3)  # rate limit 방지

        logger.info(f"메인 메시지 + {len(postings)}건 스레드 전송 완료")
        return True

    def _build_posting_blocks(self, posting: dict, index: int, total: int) -> List[dict]:
        """개별 공고 스레드 댓글용 블록"""
        cat = posting.get("category", "")
        tag = f"[{cat}] " if cat else ""

        parts = [f"*{index}/{total}  {tag}{posting['title']}*"]

        if posting.get("organization"):
            parts.append(f":office:  소관기관: {posting['organization']}")
        if posting.get("start_date") and posting.get("end_date"):
            parts.append(f":calendar:  신청기간: {posting['start_date']} ~ {posting['end_date']}")
        elif posting.get("end_date"):
            parts.append(f":calendar:  마감일: {posting['end_date']}")
        if posting.get("target"):
            parts.append(f":bust_in_silhouette:  지원대상: {posting['target']}")
        if posting.get("summary"):
            summary = posting["summary"][:200]
            parts.append(f":page_facing_up:  {summary}")

        text = "\n".join(parts)

        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text[:3000]},
            },
        ]

        if posting.get("url"):
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":link: 상세보기"},
                        "url": posting["url"],
                    }
                ],
            })

        return blocks

    def _send_no_updates(self) -> bool:
        """신규 공고 없을 때 메시지"""
        today = datetime.now().strftime("%Y-%m-%d")
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":memo: *{today}* - 오늘 신규 스타트업/해외진출 관련 공고가 없습니다.",
                },
            }
        ]
        ts = self._post_message(blocks, "오늘 신규 공고 없음")
        return ts is not None

    def _post_message(
        self, blocks: List[dict], fallback_text: str, thread_ts: Optional[str] = None
    ) -> Optional[str]:
        """Slack chat.postMessage 호출. 성공 시 message ts 반환."""
        payload = {
            "channel": self.channel,
            "text": fallback_text,
            "blocks": blocks,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts

        try:
            resp = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10,
            )
            data = resp.json()
            if data.get("ok"):
                return data.get("ts")
            else:
                logger.error(f"Slack API 에러: {data.get('error')}")
                return None
        except requests.RequestException as e:
            logger.error(f"Slack 전송 오류: {e}")
            return None
