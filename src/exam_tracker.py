"""시험 등록 추적 유틸리티"""
from datetime import datetime, timezone, timedelta

from . import calendar_service as cal

TAG = "#시험관리"
MILESTONE_ICONS = {"접수마감": "📋", "시험일": "📝", "결과발표": "🏆"}


def _make_description(cert: str, session: str, milestone: str) -> str:
    return f"{TAG} 자격증={cert} 회차={session} 단계={milestone}"


def _parse_meta(description: str) -> dict | None:
    if not description or TAG not in description:
        return None
    meta = {}
    for token in description.split():
        if "=" in token:
            k, v = token.split("=", 1)
            meta[k] = v
    return meta if "자격증" in meta and "단계" in meta else None


def create_exam_events(
    cert: str,
    session: str,
    시험일: str,
    접수마감: str = "",
    결과발표: str = "",
    calendar_id: str = "primary",
) -> list[dict]:
    milestones = []
    if 접수마감:
        milestones.append(("접수마감", 접수마감))
    milestones.append(("시험일", 시험일))
    if 결과발표:
        milestones.append(("결과발표", 결과발표))

    events = []
    for milestone, date in milestones:
        title = f"📜 [자격증] {cert} {session} - {milestone}"
        desc = _make_description(cert, session, milestone)
        event = cal.add_event(title, date, desc, calendar_id)
        events.append(event)
    return events


def get_active_exams(calendar_id: str = "primary") -> dict[str, dict]:
    """진행 중인 시험 목록을 그룹별로 반환한다."""
    now = datetime.now(tz=timezone.utc)
    time_min = (now - timedelta(days=30)).isoformat()
    time_max = (now + timedelta(days=365)).isoformat()

    events = cal.get_events_range(time_min, time_max, calendar_id)

    groups: dict[str, dict] = {}
    for event in events:
        desc = event.get("description", "") or ""
        meta = _parse_meta(desc)
        if not meta:
            continue

        cert = meta["자격증"]
        session = meta.get("회차", "")
        milestone = meta["단계"]
        key = f"{cert}|{session}"

        if key not in groups:
            groups[key] = {"cert": cert, "session": session, "milestones": []}

        groups[key]["milestones"].append({
            "milestone": milestone,
            "date": cal.get_event_date(event),
            "dday": cal.calc_dday(event),
        })

    # 마일스톤이 모두 D+2 이상 지난 그룹(완전히 끝난 시험)은 제외
    return {
        key: group
        for key, group in groups.items()
        if any(m["dday"] >= -1 for m in group["milestones"])
    }
