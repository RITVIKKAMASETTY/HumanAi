import re
import uuid
from datetime import datetime
from typing import Optional

import spacy

TITLE_KEYS = [
    "program title", "grant title", "opportunity title", "solicitation title",
    "award title", "project title", "title",
]

AGENCY_KEYS = [
    "funding agency", "sponsoring agency", "federal agency", "lead agency",
    "agency", "sponsor", "organization", "directorate",
]

CLOSE_DATE_KEYS = [
    "application deadline", "submission deadline", "proposal deadline",
    "due date", "closing date", "close date", "deadline",
]

OPEN_DATE_KEYS = [
    "open date", "release date", "publish date", "posted date",
    "issuance date", "start date",
]

ELIGIBILITY_KEYS = [
    "eligibility information", "eligible applicants", "who may apply",
    "eligibility requirements", "eligibility",
]

DESCRIPTION_KEYS = [
    "program description", "program summary", "project description",
    "synopsis", "overview", "abstract", "introduction",
]

AWARD_KEYS = [
    "award information", "award amount", "anticipated funding amount",
    "estimated total program funding", "award size", "award ceiling",
    "award floor", "funding amount", "budget",
]

MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08", "sep": "09",
    "oct": "10", "nov": "11", "dec": "12",
}

try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    _nlp = None


def extract_fields(parsed: dict, source_url: str) -> dict:
    soup = parsed.get("soup")
    plain_text = parsed.get("plain_text", "")
    sections = parsed.get("sections", {})

    foa_id = _extract_foa_id(plain_text, source_url) or str(uuid.uuid4())
    title = _from_soup_meta(soup) or _from_sections(sections, TITLE_KEYS) or _from_label(plain_text, TITLE_KEYS) or _soup_h1(soup)
    agency = _from_sections(sections, AGENCY_KEYS) or _from_label(plain_text, AGENCY_KEYS) or _spacy_org(plain_text) or "National Science Foundation"
    close_date = _parse_iso_date(_from_sections(sections, CLOSE_DATE_KEYS) or _from_label(plain_text, CLOSE_DATE_KEYS) or _regex_date(plain_text, ["deadline", "due", "close", "submit"]))
    open_date = _parse_iso_date(_from_sections(sections, OPEN_DATE_KEYS) or _from_label(plain_text, OPEN_DATE_KEYS) or _regex_date(plain_text, ["open", "release", "posted", "issuance"]))
    eligibility = _from_sections(sections, ELIGIBILITY_KEYS) or _from_label(plain_text, ELIGIBILITY_KEYS)
    description = _from_sections(sections, DESCRIPTION_KEYS) or _from_label(plain_text, DESCRIPTION_KEYS) or _fallback_description(plain_text)
    return {
        "foa_id": foa_id,
        "opportunity_number": sections.get("opportunity number"),
        "title": _clean(title),
        "agency": _clean_single_line(agency) or "National Science Foundation",
        "open_date": open_date,
        "close_date": close_date,
        "archive_date": sections.get("archive date"),
        "eligibility": _clean(eligibility) or _clean(sections.get("eligibility")),
        "expected_awards": sections.get("expected awards"),
        "award_floor": sections.get("award floor"),
        "award_ceiling": sections.get("award ceiling"),
        "total_program_funding": sections.get("total program funding"),
        "cost_sharing_required": sections.get("cost sharing"),
        "cfda_numbers": sections.get("cfda"),
        "contact_name": sections.get("contact name"),
        "contact_email": sections.get("contact email"),
        "funding_instrument": sections.get("funding instrument"),
        "activity_category": sections.get("activity category"),
        "description": _clean(description),
        "source_url": source_url,
    }


def _extract_foa_id(text: str, url: str) -> Optional[str]:
    patterns = [
        r"NSF[- ]?\d{2}[-]\d{3}",
        r"PD[-\s]?\d{2}[-]\d+",
        r"FOA[-\s]?\d{4}",
        r"PA[-\s]?\d{2}[-]\d+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).upper().replace(" ", "-")

    url_match = re.search(r"nsf\d{2}-\d{3}", url, re.IGNORECASE)
    if url_match:
        return url_match.group(0).upper()

    return None


def _from_soup_meta(soup) -> Optional[str]:
    if soup is None:
        return None
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"]
    tag = soup.find("title")
    if tag:
        raw = tag.get_text(strip=True)
        raw = re.sub(r"\s*[\|\-–]\s*NSF.*$", "", raw, flags=re.IGNORECASE).strip()
        return raw if len(raw) > 10 else None
    return None


def _soup_h1(soup) -> Optional[str]:
    if soup is None:
        return None
    tag = soup.find("h1")
    return tag.get_text(strip=True) if tag else None


def _from_sections(sections: dict, keys: list) -> Optional[str]:
    for key in keys:
        for section_name, content in sections.items():
            if key in section_name:
                return content
    return None


def _from_label(text: str, keys: list) -> Optional[str]:
    for key in keys:
        pattern = rf"(?i)(?:^|\n)\s*{re.escape(key)}\s*[:\-]\s*(.+?)(?=\n[A-Z]|\n\n|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            value = match.group(1).strip()
            if 3 < len(value) < 2000:
                return value
    return None


def _regex_date(text: str, context_words: list) -> Optional[str]:
    month_pattern = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    date_pattern = rf"{month_pattern}\s+\d{{1,2}},?\s+\d{{4}}|\d{{1,2}}/\d{{1,2}}/\d{{2,4}}|\d{{4}}-\d{{2}}-\d{{2}}"

    for word in context_words:
        window_pattern = rf"(?i){word}[^\n]{{0,60}}?({date_pattern})|({date_pattern})[^\n]{{0,30}}?{word}"
        match = re.search(window_pattern, text)
        if match:
            return match.group(1) or match.group(2)

    match = re.search(date_pattern, text)
    return match.group(0) if match else None


def _parse_iso_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    raw = raw.strip()

    iso_match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    if iso_match:
        return iso_match.group(0)

    slash_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", raw)
    if slash_match:
        m, d, y = slash_match.groups()
        y = "20" + y if len(y) == 2 else y
        return f"{y}-{int(m):02d}-{int(d):02d}"

    month_match = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})",
        raw, re.IGNORECASE,
    )
    if month_match:
        month_name, day, year = month_match.groups()
        month_num = MONTHS.get(month_name.lower()[:3])
        if month_num:
            return f"{year}-{month_num}-{int(day):02d}"

    return None


def _regex_award(text: str) -> Optional[str]:
    patterns = [
        r"\$[\d,]+(?:\s*(?:to|-)\s*\$[\d,]+)?(?:\s*(?:million|thousand|M|K))?",
        r"up to \$[\d,]+(?:\s*(?:million|thousand|M|K))?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _spacy_org(text: str) -> Optional[str]:
    if _nlp is None:
        return None
    doc = _nlp(text[:5000])
    orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
    if orgs:
        return orgs[0]
    return None


def _fallback_description(text: str) -> Optional[str]:
    sentences = [s.strip() for s in text.split("\n") if len(s.strip()) > 80]
    if sentences:
        return " ".join(sentences[:3])
    return None


def _clean(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value if value else None


def _clean_single_line(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    first_line = value.split("\n")[0]
    return _clean(first_line)
