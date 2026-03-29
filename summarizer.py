# -*- coding: utf-8 -*-
"""영상 자막 추출 + LLM 요약 (이메일용 HTML 반환)."""
from __future__ import annotations

import logging
import re
from typing import Optional

from youtube_fetcher import VideoInfo

logger = logging.getLogger(__name__)


def get_transcript(video_id: str) -> Optional[str]:
    """자막 추출. 한국어 우선 → 영어 → None."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

        api = YouTubeTranscriptApi()

        # 한국어 → 영어 순서로 시도
        for lang in (["ko"], ["en"], None):
            try:
                if lang is None:
                    # 마지막 시도: 사용 가능한 아무 자막
                    fetched = api.fetch(video_id)
                else:
                    fetched = api.fetch(video_id, languages=lang)
                text = " ".join(s.text for s in fetched)
                return text.strip() if text else None
            except NoTranscriptFound:
                continue
            except TranscriptsDisabled:
                return None
            except Exception as e:
                logger.warning("자막 추출 오류 (IP 차단 의심): %s", e)
                return None
        return None
    except ImportError:
        return None


def summarize_video_html(video: VideoInfo) -> str:
    """영상을 요약하여 이메일용 HTML <li> 요소로 반환합니다."""
    transcript = get_transcript(video.video_id)
    if not transcript:
        return f'<li><strong>{video.channel_title}</strong> - {video.title}<br>[자막 없음 - 요약 불가]<br><a href="{video.url}">[영상 보기]</a></li>\n'

    from config import GEMINI_API_KEY, GEMINI_MODEL
    from google import genai
    from google.genai import types

    if not GEMINI_API_KEY:
        return f'<li><strong>{video.channel_title}</strong> - {video.title}<br>[Gemini API 키 없음]<br><a href="{video.url}">[영상 보기]</a></li>\n'

    # 프롬프트 길이 제한 방어 (2만자)
    if len(transcript) > 20000:
        transcript = transcript[:20000] + "\n[...중략...]"

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""당신은 유튜브 영상 자막을 읽고 핵심 내용을 3~4문장으로 요약하는 큐레이터입니다. 한국어로 자연스럽게 의역하세요. 

출력 규칙 (반드시 지키세요):
- 순수 텍스트만 출력하세요. HTML <li> 안에 들어갈 텍스트입니다.
- 마크다운(```)이나 리스트 기호(-, *)를 과도하게 쓰지 말고 문장 형태로 이어 쓰세요.

영상 제목: {video.title}
채널명: {video.channel_title}

자막:
{transcript}"""
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=1000, temperature=0.3)
        )
        
        summary = response.text.strip()
        
        # 마크다운 블록이나 불필요한 기호 제거
        summary = re.sub(r"^```(?:html|text)?\s*", "", summary, flags=re.IGNORECASE)
        summary = re.sub(r"\s*```$", "", summary)
        
        # 줄바꿈을 <br>로 치환하여 깨끗한 HTML 문단 만들기
        summary_html = summary.replace("\n", "<br>")
        
        return (
            f'<li>'
            f'<strong>{video.channel_title}</strong> - <strong>{video.title}</strong><br>'
            f'<span style="color: #444;">{summary_html}</span><br>'
            f'<a href="{video.url}" style="font-size: 0.9em; color: #1a73e8;">[▶️ 영상 보기]</a>'
            f'</li>\n'
        )
    except Exception as e:
        logger.exception("요약 실패: %s", video.video_id)
        return (
            f'<li>'
            f'<strong>{video.channel_title}</strong> - {video.title}<br>'
            f'<span style="color: red;">[요약 실패: {e}]</span><br>'
            f'<a href="{video.url}">[영상 보기]</a>'
            f'</li>\n'
        )
