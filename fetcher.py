import io
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; FOA-Pipeline/1.0; "
        "+https://github.com/humanai-foundation/foa-pipeline)"
    )
}

TIMEOUT = 20


def fetch(url: str) -> dict:
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
        "raw_bytes": response.content,
        "text": response.text if not is_pdf else None,
    }
