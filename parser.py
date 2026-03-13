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


def parse_json(data: dict) -> dict:
    synopsis = data.get("synopsis", {})
    
    # Map Grants.gov JSON fields to standard sections
    sections = {}
    if data.get("opportunityNumber"):
        sections["opportunity number"] = data["opportunityNumber"]
    if data.get("opportunityTitle"):
        sections["opportunity title"] = data["opportunityTitle"]
    if synopsis.get("agencyName"):
        sections["agency"] = synopsis["agencyName"]
    # Extract Description Text cleanly
    if synopsis.get("synopsisDesc"):
        # The user reported words being cut off (e.g., 'ngineering (ECLIPSE)' instead of 'Engineering (ECLIPSE)')
        # BS4 get_text sometimes joins without spaces if the HTML is weird. Add a space separator.
        soup = BeautifulSoup(synopsis["synopsisDesc"], "html.parser")
        sections["description"] = soup.get_text(separator=" ", strip=True)
    
    # Handle discrete Award values
    def _safe_format(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    floor = _safe_format(synopsis.get("awardFloor"))
    if floor is not None:
        sections["award floor"] = floor
        
    ceiling = _safe_format(synopsis.get("awardCeiling"))
    if ceiling is not None:
        sections["award ceiling"] = ceiling
        
    total = _safe_format(synopsis.get("estimatedTotalProgramFunding"))
    if total is not None:
        sections["total program funding"] = total
        
    # Cost Sharing
    if synopsis.get("costSharing") is not None:
        sections["cost sharing"] = synopsis.get("costSharing")
        
    # Expected Awards
    if synopsis.get("expectedNumberOfAwards") is not None:
        sections["expected awards"] = synopsis.get("expectedNumberOfAwards")
        
    # Additional Deep Metadata
    # CFDA numbers are usually stored in the 'cfdas' list as 'cfdaNumber'
    cfdas = [c.get("cfdaNumber") for c in data.get("cfdas", []) if c.get("cfdaNumber")]
    if cfdas:
        sections["cfda"] = ", ".join(cfdas)
        
    # Agency Contact (The 'agencyContactDesc' often has the real underlying contact name/info)
    contact_desc = synopsis.get("agencyContactDesc", "")
    if contact_desc:
        sections["contact name"] = contact_desc.split("\n")[0].strip()
    elif synopsis.get("agencyContactName"):
        sections["contact name"] = synopsis.get("agencyContactName")
        
    if synopsis.get("agencyContactEmail"):
        sections["contact email"] = synopsis.get("agencyContactEmail")
        
    instruments = synopsis.get("fundingInstruments", [])
    if instruments:
        sections["funding instrument"] = "; ".join(i.get("description", "") for i in instruments)
        
    activities = synopsis.get("fundingActivityCategories", [])
    if activities:
        sections["activity category"] = "; ".join(a.get("description", "") for a in activities)
        
    if synopsis.get("archiveDateStr"):
        date_str = synopsis.get("archiveDateStr")
        # Format "2026-12-16-00-00-00" to "2026-12-16"
        sections["archive date"] = date_str.split("-00-00")[0]
        
    # Handle Eligibility
    applicants = synopsis.get("applicantTypes", [])
    if applicants:
        sections["eligibility"] = "; ".join(a.get("description", "") for a in applicants)
    
    # Add dates
    if data.get("openDate") or synopsis.get("postingDateStr"):
        sections["open date"] = synopsis.get("postingDateStr") or data.get("openDate")
    if data.get("closeDate") or synopsis.get("responseDateStr"):
        sections["close date"] = synopsis.get("responseDateStr") or data.get("closeDate")

    plain_text = "\n".join(f"{k}: {v}" for k, v in sections.items())
    return {"soup": None, "plain_text": plain_text, "sections": sections}


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
