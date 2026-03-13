import io
import json
import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; FOA-Pipeline/1.0; "
        "+https://github.com/humanai-foundation/foa-pipeline)"
    )
}

TIMEOUT = 20


def fetch(url: str) -> dict:
    if "grants.gov" in url and "search-results-detail" in url:
        return _fetch_grants_gov_api(url)

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc

    content_type = response.headers.get("content-type", "").lower()
    is_pdf = "pdf" in content_type or url.lower().endswith(".pdf")

    return {
        "url": url,
        "content_type": content_type,
        "is_pdf": is_pdf,
        "is_json": False,
        "raw_bytes": response.content,
        "text": response.text if not is_pdf else None,
        "json_data": None,
    }


def _fetch_grants_gov_api(url: str) -> dict:
    match = re.search(r"search-results-detail/(\d+)", url)
    if not match:
        raise RuntimeError(f"Could not extract oppId from Grants.gov URL: {url}")
    opp_id = match.group(1)

    api_url = "https://apply07.grants.gov/grantsws/rest/opportunity/details"
    payload = {"oppId": opp_id}

    try:
        resp = requests.post(
            api_url, 
            data=payload, 
            headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch Grants.gov API for {opp_id}: {exc}") from exc

    return {
        "url": url,
        "content_type": "application/json",
        "is_pdf": False,
        "is_json": True,
        "raw_bytes": None,
        "text": None,
        "json_data": data,
    }
