# -*- coding: utf-8 -*-
"""
GitHub Actions용 메인 스크립트.
한 번 실행 → 새 영상 요약 → 이메일 발송 → 종료.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

# 현재 경로를 시스템 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from storage import is_seen, mark_seen
from summarizer import summarize_video_html
from youtube_fetcher import get_new_videos
from email_sender import send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_daily_job():
    logger.info("=" * 60)
    logger.info("유튜브 요약 ই메일 봇 시작: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    # 1. 새 영상 조회
    logger.info("[1/3] 새 영상 조회 중...")
    try:
        videos = get_new_videos()
    except ValueError as e:
        logger.error("영상 조회 풀링 실패: %s", e)
        sys.exit(1)

    new_ones = [v for v in videos if not is_seen(v.video_id)]

    if not new_ones:
        logger.info("🆕 오늘 등록된 새 영상이 없습니다. 이메일을 보내지 않습니다.")
        return

    logger.info("[2/3] 새 영상 %d개 요약 시작...", len(new_ones))
    
    html_items = []
    
    # 2. 개별 영상 요약
    for idx, video in enumerate(new_ones, 1):
        logger.info("  [%d/%d] %s", idx, len(new_ones), video.title)
        
        # HTML <li> 구조 형태로 요약된 문자열을 받아옵니다.
        html_list_item = summarize_video_html(video)
        html_items.append(html_list_item)
        
        # 본 것으로 마킹
        mark_seen(video.video_id, video.channel_id, video.channel_title, video.title)

    # 3. HTML 조립 및 이메일 발송
    logger.info("[3/3] 이메일 발송 중...")
    
    html_body = "<h2>📺 새로 올라온 유튜브 영상 요약</h2>\n<ul>\n"
    for item in html_items:
        html_body += item + "<br>\n"
    html_body += "</ul>\n"
    
    today = datetime.now().strftime("%Y년 %m월 %d일")
    subject = f"📺 [유튜브 요약] 오늘의 새 영상 - {today}"
    
    success = send_email(html_body=html_body, subject=subject)
    
    if success:
        logger.info("✅ 전체 %d개 요약 이메일 발송 성공!", len(new_ones))
    else:
        logger.error("❌ 이메일 발송 실패!")


if __name__ == "__main__":
    run_daily_job()
