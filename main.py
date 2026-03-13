import argparse
import sys

from fetcher import fetch
from parser import parse_html, parse_pdf
from extractor import extract_fields
from tagger import tag
from exporter import export


def build_pipeline(url: str, out_dir: str) -> None:
    print(f"Fetching: {url}")
    response = fetch(url)

    if response["is_pdf"]:
        print("Detected PDF content")
        parsed = parse_pdf(response["raw_bytes"])
    else:
        print("Detected HTML content")
        parsed = parse_html(response["text"])

    print("Extracting fields")
    foa = extract_fields(parsed, url)

    print("Applying semantic tags")
    tags = tag(foa)

    print(f"Exporting to {out_dir}")
    paths = export(foa, tags, out_dir)

    print(f"  JSON: {paths['json']}")
    print(f"  CSV:  {paths['csv']}")
    print("Done")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a single NSF FOA URL and export structured JSON + CSV."
    )
    parser.add_argument("--url", required=True, help="FOA page URL (HTML or PDF)")
    parser.add_argument("--out_dir", required=True, help="Output directory for foa.json and foa.csv")
    args = parser.parse_args()

    try:
        build_pipeline(args.url, args.out_dir)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()