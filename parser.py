import io
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text as pdf_extract_text


def parse_html(html_text: str) -> dict:
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    plain_text = soup.get_text(separator="\n", strip=True)
    sections = _extract_sections(soup)

    return {"soup": soup, "plain_text": plain_text, "sections": sections}


def parse_pdf(raw_bytes: bytes) -> dict:
    byte_stream = io.BytesIO(raw_bytes)
    plain_text = pdf_extract_text(byte_stream) or ""
    return {"soup": None, "plain_text": plain_text, "sections": {}}


def _extract_sections(soup: BeautifulSoup) -> dict:
    sections = {}
    headings = soup.find_all(["h1", "h2", "h3", "h4"])

    for heading in headings:
        heading_text = heading.get_text(strip=True)
        if not heading_text:
            continue

        content_parts = []
        for sibling in heading.find_next_siblings():
            if sibling.name in {"h1", "h2", "h3", "h4"}:
                break
            text = sibling.get_text(separator=" ", strip=True)
            if text:
                content_parts.append(text)

        if content_parts:
            sections[heading_text.lower()] = " ".join(content_parts)

    return sections
