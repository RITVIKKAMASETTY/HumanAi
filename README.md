# FOA Pipeline — HumanAI GSoC 2026 Screening Task

A modular pipeline that ingests a single Funding Opportunity Announcement (FOA) URL from NSF, extracts structured fields, applies hybrid semantic tags, and exports `foa.json` and `foa.csv`.

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Usage

```bash
python main.py --url "<NSF FOA URL>" --out_dir ./out
```

**Example:**

```bash
python main.py \
  --url "https://www.nsf.gov/funding/opportunities/pose-pathways-enable-open-source-ecosystems/505982/nsf24-606/solicitation" \
  --out_dir ./out
```

Outputs:
- `out/foa.json` — full structured record with nested tags
- `out/foa.csv` — flat record with semicolon-separated tags

## Architecture

```
main.py
  └── fetcher.py       HTTP fetch, content-type detection (HTML vs PDF)
  └── parser.py        BeautifulSoup (HTML), pdfminer (PDF), section extraction
  └── extractor.py     4-layer field extraction + spaCy NER
  └── tagger.py        Hybrid rule-based + sentence-transformers semantic tagging
  └── exporter.py      JSON + CSV export
  └── ontology.py      Controlled ontology definitions and rule keywords
```

### Extraction Layers

1. **Soup meta** — `<meta property="og:title">`, `<title>` tag
2. **Section map** — heading → content extracted from all `h1–h4` elements
3. **Label regex** — multi-synonym label matching across synonyms (`Grant Title`, `Program Title`, etc.)
4. **Fallback heuristics** — spaCy NER for orgs, regex date detection, first long paragraphs

### Tagging

Hybrid approach across four ontology categories:
- `research_domains`
- `methods`
- `populations`
- `sponsor_themes`

Rule-based pass runs first (fast, deterministic). `all-MiniLM-L6-v2` sentence embeddings then fill gaps for unlabeled candidates above cosine similarity threshold `0.30`.

## Output Schema

```json
{
  "foa_id": "NSF24-606",
  "title": "...",
  "agency": "National Science Foundation",
  "open_date": "2024-01-15",
  "close_date": "2024-06-01",
  "eligibility": "...",
  "description": "...",
  "award_range": "$500,000",
  "source_url": "https://...",
  "tags": {
    "research_domains": ["Computer Science", "Artificial Intelligence"],
    "methods": ["Optimization"],
    "populations": ["Researchers"],
    "sponsor_themes": ["Open Source", "Innovation"]
  }
}
```

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP fetching |
| `beautifulsoup4` | HTML parsing |
| `pdfminer.six` | PDF text extraction |
| `spacy` (en_core_web_sm) | Named entity recognition |
| `sentence-transformers` | Semantic similarity tagging |
| `numpy` | Cosine similarity computation |
