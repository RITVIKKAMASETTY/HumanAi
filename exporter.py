import csv
import json
import os
from typing import Optional


def export(foa: dict, tags: dict, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    record = _build_record(foa, tags)

    json_path = os.path.join(out_dir, "foa.json")
    csv_path = os.path.join(out_dir, "foa.csv")

    _write_json(record, json_path)
    _write_csv(record, csv_path)

    return {"json": json_path, "csv": csv_path}


def _build_record(foa: dict, tags: dict) -> dict:
    record = dict(foa)
    record["tags"] = {
        "research_domains": tags.get("research_domains", []),
        "methods": tags.get("methods", []),
        "populations": tags.get("populations", []),
        "sponsor_themes": tags.get("sponsor_themes", []),
    }
    return record


def _write_json(record: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)


def _write_csv(record: dict, path: str) -> None:
    flat = dict(record)
    tags = flat.pop("tags", {})
    for key, values in tags.items():
        flat[key] = "; ".join(values) if values else ""

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(flat.keys()))
        writer.writeheader()
        writer.writerow(flat)
