import os
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = Path(__file__).parent.parent


def _ensure_credentials_files():
    """환경변수에서 Google 인증 파일을 복원한다 (Docker/클라우드 배포용)."""
    token_path = BASE_DIR / "token.json"
    credentials_path = BASE_DIR / "credentials.json"

    if not token_path.exists():
        token_json = os.getenv("GOOGLE_TOKEN_JSON")
        if token_json:
            token_path.write_text(token_json)

    if not credentials_path.exists():
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            credentials_path.write_text(creds_json)


def get_calendar_service():
    _ensure_credentials_files()
    creds = None
    token_path = BASE_DIR / "token.json"
    credentials_path = BASE_DIR / "credentials.json"

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def add_event(title: str, date: str, description: str = "", calendar_id: str = "primary") -> dict:
    """날짜 형식: YYYY-MM-DD 또는 YYYY-MM-DD HH:MM"""
    service = get_calendar_service()

    if len(date) == 10:  # YYYY-MM-DD
        event_body = {
            "summary": title,
            "description": description,
            "start": {"date": date, "timeZone": "Asia/Seoul"},
            "end": {"date": date, "timeZone": "Asia/Seoul"},
        }
    else:  # YYYY-MM-DD HH:MM
        dt = datetime.strptime(date, "%Y-%m-%d %H:%M")
        start_iso = dt.isoformat()
        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_iso, "timeZone": "Asia/Seoul"},
            "end": {"dateTime": start_iso, "timeZone": "Asia/Seoul"},
        }

    event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
    return event


def get_events_range(time_min: str, time_max: str, calendar_id: str = "primary") -> list[dict]:
    service = get_calendar_service()
    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])


def list_events(year: int, month: int, calendar_id: str = "primary") -> list[dict]:
    service = get_calendar_service()

    time_min = datetime(year, month, 1, tzinfo=timezone.utc).isoformat()
    if month == 12:
        time_max = datetime(year + 1, 1, 1, tzinfo=timezone.utc).isoformat()
    else:
        time_max = datetime(year, month + 1, 1, tzinfo=timezone.utc).isoformat()

    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])


def get_upcoming_events(days: int = 7, calendar_id: str = "primary") -> list[dict]:
    service = get_calendar_service()

    now = datetime.now(tz=timezone.utc)
    time_min = now.isoformat()
    from datetime import timedelta
    time_max = (now + timedelta(days=days)).isoformat()

    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])


def get_event_date(event: dict) -> str:
    start = event.get("start", {})
    return start.get("date") or start.get("dateTime", "")[:10]


def calc_dday(event: dict) -> int:
    date_str = get_event_date(event)
    if not date_str:
        return 9999
    event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    return (event_date - today).days
