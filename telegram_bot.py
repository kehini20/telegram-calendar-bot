from telegram.ext import Updater, MessageHandler, Filters
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import re
from datetime import datetime, timedelta
import os
import json
from google.oauth2.credentials import Credentials

# 구글 인증
# 환경 변수에서 token.json 내용 불러오기
token_data = json.loads(os.environ['GOOGLE_TOKEN_JSON'])
creds = Credentials.from_authorized_user_info(token_data, ['https://www.googleapis.com/auth/calendar'])
service = build('calendar', 'v3', credentials=creds)

# 날짜/시간/지속시간 + 제목 추출 함수
def extract_datetime_title_duration(text):
    pattern = r'(\d{1,2})월\s*(\d{1,2})일\s*(오전|오후)?\s*(\d{1,2})시(?:\s*(\d{1,2})분)?'
    time_match = re.search(pattern, text)
    if not time_match:
        return None, None, None

    month = int(time_match.group(1))
    day = int(time_match.group(2))
    meridian = time_match.group(3)
    hour = int(time_match.group(4))
    minute = int(time_match.group(5)) if time_match.group(5) else 0

    if meridian == '오후' and hour != 12:
        hour += 12
    elif meridian == '오전' and hour == 12:
        hour = 0

    now = datetime.now()
    try:
        start_time = datetime(year=now.year, month=month, day=day, hour=hour, minute=minute)
    except ValueError:
        return None, None, None

    duration_pattern = r'(\d+)\s*(분|시간)'
    duration_match = re.search(duration_pattern, text)
    duration = 60
    if duration_match:
        number = int(duration_match.group(1))
        unit = duration_match.group(2)
        duration = number * 60 if unit == '시간' else number

    # 제목에서 날짜와 시간, 지속시간 부분 제거
    remove_parts = [time_match.group(0)]
    if duration_match:
        remove_parts.append(duration_match.group(0))
    title = text
    for part in remove_parts:
        title = title.replace(part, "")
    title = title.strip()

    return start_time, title, duration

# 메시지 처리
def handle_message(update, context):
    text = update.message.text.strip()
    print(f"입력된 메시지: {text}")

    start_time, title, duration = extract_datetime_title_duration(text)
    if not start_time or not title:
        update.message.reply_text("날짜/시간/지속시간을 이해할 수 없어요!\n예: 4월 6일 오후 5시 아이브 팬 콘서트 90분")
        return

    end_time = start_time + timedelta(minutes=duration)

    event = {
        'summary': title,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Seoul'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Seoul'},
    }

    service.events().insert(calendarId='primary', body=event).execute()
    update.message.reply_text(f"일정이 등록됐어요:\n[{title}] {start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%H:%M')}")

# 봇 설정
updater = Updater("7508822610:AAGMTGWZ4dx7Pw69xf2L_Zm6z0KegFCoLh4", use_context=True)
dp = updater.dispatcher
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
updater.start_polling()
updater.idle()
