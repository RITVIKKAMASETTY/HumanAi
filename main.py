import argparse
import sys
import os
import warnings
import logging
from src.fetcher import fetch
from src.parser import parse_html, parse_pdf, parse_json
from src.extractor import extract_fields
from src.tagger import tag
from src.exporter import export

# Suppress all the noisy 3rd party warnings (spaCy, HuggingFace, sentence-transformers)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


class Colors:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


def build_pipeline(url: str, out_dir: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE} Starting FOA Extraction Pipeline{Colors.ENDC}")
    print(f"{Colors.CYAN}➤ Fetching:{Colors.ENDC} {url}")
    response = fetch(url)

    if response.get("is_json"):
        print(f"{Colors.GREEN}✓ Detected JSON API content{Colors.ENDC}")
        parsed = parse_json(response["json_data"])
    elif response.get("is_pdf"):
        print(f"{Colors.GREEN}✓ Detected PDF content{Colors.ENDC}")
        parsed = parse_pdf(response["raw_bytes"])
    else:
        print(f"{Colors.GREEN}✓ Detected HTML content{Colors.ENDC}")
        parsed = parse_html(response["text"])

    print(f"{Colors.CYAN}➤ Extracting fields{Colors.ENDC}")
    foa = extract_fields(parsed, url)

    print(f"{Colors.CYAN}➤ Applying semantic tags{Colors.ENDC}")
    tags = tag(foa)

    print(f"{Colors.CYAN}➤ Exporting to {out_dir}{Colors.ENDC}")
    paths = export(foa, tags, out_dir)

    print(f"  {Colors.BOLD}JSON:{Colors.ENDC} {paths['json']}")
    print(f"  {Colors.BOLD}CSV:{Colors.ENDC}  {paths['csv']}")
    print(f"\n{Colors.BOLD}{Colors.GREEN}✨ Done! FOA pipeline execution completed successfully.{Colors.ENDC}\n")


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
        print(f"{Colors.RED}{Colors.BOLD}Error:{Colors.ENDC} {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()