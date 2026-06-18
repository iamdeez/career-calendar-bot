"""주요 IT 자격증 정보 (국내 기준)"""

CERTIFICATIONS = {
    "정보처리기사": {
        "alias": ["정처기", "정보처리"],
        "org": "한국산업인력공단",
        "url": "https://www.q-net.or.kr",
        "schedule_note": "연 3회 시행 (필기·실기 각각)",
    },
    "정보보안기사": {
        "alias": ["보안기사"],
        "org": "한국인터넷진흥원(KISA)",
        "url": "https://www.kisa.or.kr",
        "schedule_note": "연 2회 시행",
    },
    "SQLD": {
        "alias": ["sql개발자", "sqld"],
        "org": "한국데이터산업진흥원",
        "url": "https://www.dataq.or.kr",
        "schedule_note": "연 4회 시행",
    },
    "SQLP": {
        "alias": ["sql전문가"],
        "org": "한국데이터산업진흥원",
        "url": "https://www.dataq.or.kr",
        "schedule_note": "연 2회 시행",
    },
    "ADsP": {
        "alias": ["데이터분석준전문가"],
        "org": "한국데이터산업진흥원",
        "url": "https://www.dataq.or.kr",
        "schedule_note": "연 4회 시행",
    },
    "AWS-SAA": {
        "alias": ["aws솔루션스아키텍트", "aws saa"],
        "org": "Amazon Web Services",
        "url": "https://aws.amazon.com/ko/certification",
        "schedule_note": "상시 시행 (피어슨 VUE)",
    },
    "정보처리산업기사": {
        "alias": ["정처산기"],
        "org": "한국산업인력공단",
        "url": "https://www.q-net.or.kr",
        "schedule_note": "연 3회 시행",
    },
    "네트워크관리사": {
        "alias": ["네관사"],
        "org": "한국정보통신자격협회",
        "url": "https://www.icqa.or.kr",
        "schedule_note": "연 4회 시행",
    },
}

CATEGORIES = {
    "자격증": "📜",
    "스터디": "📚",
    "공채": "💼",
    "인턴": "🏢",
    "해커톤": "💻",
    "컨퍼런스": "🎤",
    "기타": "📌",
}


def find_cert(name: str) -> tuple[str, dict] | tuple[None, None]:
    name_lower = name.lower().replace(" ", "")
    for cert_name, info in CERTIFICATIONS.items():
        if name_lower in cert_name.lower().replace(" ", ""):
            return cert_name, info
        for alias in info.get("alias", []):
            if name_lower in alias.lower().replace(" ", ""):
                return cert_name, info
    return None, None


def get_category_emoji(category: str) -> str:
    return CATEGORIES.get(category, "📌")
