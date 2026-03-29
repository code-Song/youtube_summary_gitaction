# -*- coding: utf-8 -*-
"""
Gmail SMTP를 통한 HTML 이메일 발송 모듈
"""
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER

logger = logging.getLogger(__name__)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587  # TLS


def send_email(html_body: str, subject: str = "") -> bool:
    """
    Gmail SMTP로 HTML 이메일을 발송합니다.

    Args:
        html_body: 이메일 본문 (HTML)
        subject:   이메일 제목 (기본값: 오늘 날짜 기반 자동 생성)

    Returns:
        성공 여부 (bool)
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
        logger.error("이메일 설정 미완료 (EMAIL_SENDER / EMAIL_PASSWORD / EMAIL_RECEIVER)")
        return False

    today = datetime.now().strftime("%Y년 %m월 %d일")
    if not subject:
        subject = f"📰 오늘의 뉴스 요약 - {today}"

    # 전체 HTML 문서 래핑
    full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
  <style>
    body {{
      font-family: 'Malgun Gothic', '맑은 고딕', Arial, sans-serif;
      background: #f4f6f9;
      margin: 0; padding: 20px;
      color: #333;
    }}
    .container {{
      max-width: 760px;
      margin: 0 auto;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      overflow: hidden;
    }}
    .header {{
      background: linear-gradient(135deg, #1a73e8, #0d47a1);
      color: white;
      padding: 28px 32px;
    }}
    .header h1 {{
      margin: 0 0 6px 0;
      font-size: 22px;
    }}
    .header p {{ margin: 0; opacity: 0.85; font-size: 14px; }}
    .content {{ padding: 28px 32px; }}
    h2 {{
      font-size: 18px;
      border-left: 4px solid #1a73e8;
      padding-left: 10px;
      margin-top: 28px;
    }}
    h3 {{
      font-size: 15px;
      color: #555;
      margin-top: 16px;
    }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 12px; line-height: 1.6; }}
    a {{ color: #1a73e8; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    small {{ color: #777; font-size: 12px; }}
    .footer {{
      background: #f0f4f8;
      text-align: center;
      padding: 16px;
      font-size: 12px;
      color: #999;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📰 오늘의 뉴스 요약</h1>
      <p>{today} · 네이버 뉴스 + Google 뉴스</p>
    </div>
    <div class="content">
      {html_body}
    </div>
    <div class="footer">
      이 메일은 자동으로 발송되었습니다. · new_summary_email 서비스
    </div>
  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECEIVER
    msg.attach(MIMEText(full_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        logger.info("이메일 발송 성공 → %s", EMAIL_RECEIVER)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail 인증 실패! '앱 비밀번호'를 사용했는지 확인하세요.")
        return False
    except Exception as exc:
        logger.error("이메일 발송 실패: %s", exc)
        return False
