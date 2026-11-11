"""Rebuild the public, aggregate-only reading of the archived notebook outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "archive" / "SupportTickets-original.ipynb"
REPORT = HERE / "FINDINGS.md"
ARCHIVE_SHA256 = "5576ab7c5a210da864716690faeedc51dce2d93543e14111062856e7f5e7bd0b"
CATEGORIES = ("Technical Issue", "Data Recovery", "Hardware Issue")


def output_text(notebook: dict, cell: int) -> str:
    outputs = notebook["cells"][cell].get("outputs", [])
    if len(outputs) != 1:
        raise ValueError(f"cell {cell}: expected one saved output")
    data = outputs[0].get("data", {})
    value = data.get("text/plain")
    if not value:
        raise ValueError(f"cell {cell}: saved text/plain output missing")
    return "".join(value) if isinstance(value, list) else value


def counts(text: str, header: str) -> Counter[str]:
    lines = text.splitlines()
    if not lines or lines[0] != header:
        raise ValueError(f"expected {header} frequency table")
    result: Counter[str] = Counter()
    for line in lines[1:]:
        if line.startswith("Name:"):
            continue
        match = re.fullmatch(r"(.+?)\s{2,}(\d+)", line)
        if not match:
            raise ValueError(f"malformed {header} row")
        result[match[1].strip()] += int(match[2])
    return result


def cross_counts(text: str, heading: str) -> dict[tuple[str, str], int]:
    lines = text.splitlines()
    if not lines or not lines[0].startswith(heading):
        raise ValueError(f"expected {heading} cross-tab")
    current = None
    result: dict[tuple[str, str], int] = {}
    for line in lines[1:]:
        if line.startswith("Name:"):
            continue
        match = re.fullmatch(r"(.*?)\s{2,}(.+?)\s{2,}(\d+)", line)
        if not match:
            raise ValueError(f"malformed {heading} row")
        if match[1].strip():
            current = match[1].strip()
        if current not in CATEGORIES:
            raise ValueError("unknown or absent category")
        key = (current, match[2].strip())
        if key in result:
            raise ValueError("duplicate cross-tab row")
        result[key] = int(match[3])
    return result


def extract(path: Path = ARCHIVE, verify_hash: bool = True) -> dict:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if verify_hash and digest != ARCHIVE_SHA256:
        raise ValueError("archive hash changed; audit the source before updating findings")
    notebook = json.loads(raw)
    shape = output_text(notebook, 17).strip()
    if shape != "(21, 2)":
        raise ValueError("unexpected input shape")
    category = counts(output_text(notebook, 38), "Category")
    priority = counts(output_text(notebook, 39), "Priority")
    eta = counts(output_text(notebook, 40), "ETA")
    by_priority = cross_counts(output_text(notebook, 41), "Category         Priority")
    by_eta = cross_counts(output_text(notebook, 42), "Category         ETA")
    total = sum(category.values())
    if total != 21 or sum(priority.values()) != total or sum(eta.values()) != total:
        raise ValueError("frequency totals do not reconcile")
    if set(category) != set(CATEGORIES) or set(priority) != {"High", "Medium"}:
        raise ValueError("unexpected category or priority labels")
    if Counter({c: sum(n for (cat, _), n in by_priority.items() if cat == c) for c in CATEGORIES}) != category:
        raise ValueError("priority cross-tab does not reconcile")
    column_totals = Counter()
    for (_, label), count in by_priority.items():
        column_totals[label] += count
    if column_totals != priority:
        raise ValueError("priority labels do not reconcile")
    if Counter({c: sum(n for (cat, _), n in by_eta.items() if cat == c) for c in CATEGORIES}) != category:
        raise ValueError("ETA cross-tab does not reconcile")
    if Counter({e: sum(n for (_, label), n in by_eta.items() if label == e) for e in eta}) != eta:
        raise ValueError("ETA labels do not reconcile")
    bounded = {e for e in eta if e.lower().startswith("within ")}
    if len(bounded) != 5:
        raise ValueError("unexpected ETA wording; review classification")
    return {"source_sha256": digest, "total": total, "category": category,
            "priority": priority, "eta": eta, "by_priority": by_priority,
            "by_eta": by_eta, "time_worded": sum(eta[e] for e in bounded)}


def render(data: dict) -> str:
    cat, pri = data["category"], data["priority"]
    vague = data["total"] - data["time_worded"]
    eta_vague_by_cat = {c: sum(n for (category, label), n in data["by_eta"].items()
                                if category == c and not label.lower().startswith("within "))
                        for c in CATEGORIES}
    return f"""# Saved-output analysis

Source notebook [`archive/SupportTickets-original.ipynb`](archive/SupportTickets-original.ipynb), SHA-256 `{data['source_sha256']}`. The command `python projects/support-triage/analyze.py --check` parses its saved `text/plain` outputs in cells 17 and 38–42, reconciles the tables, and checks the published report text. No model call or private dataset is needed.

| Saved output | Count |
| --- | ---: |
| Input tickets | {data['total']} |
| Technical Issue | {cat['Technical Issue']} |
| Data Recovery | {cat['Data Recovery']} |
| Hardware Issue | {cat['Hardware Issue']} |
| High priority | {pri['High']} |
| Medium priority | {pri['Medium']} |
| Low priority | 0 |
| Distinct ETA strings | {len(data['eta'])} |
| ETA strings beginning “Within” | {data['time_worded']} tickets |
| Conditional or unbounded ETA strings | {vague} tickets |

## What the outputs reveal

**Priority has little sorting power in this sample.** The model marked {pri['High']}/{data['total']} tickets High ({pri['High']/data['total']:.1%}); the only Medium ticket is Technical Issue. All {cat['Data Recovery']} Data Recovery and {cat['Hardware Issue']} Hardware Issue tickets are High. A queue using this label would still need another decision rule for nearly every ticket. These are model assignments, not verified severities.

**ETA is neither a consistent resolution estimate nor a measured time.** There are {len(data['eta'])} distinct phrases for {data['total']} tickets. {data['time_worded']} begin with “Within,” but some explicitly refer to initial assessment or first contact, and one is conditional on parts. The other {vague} use language such as “varies” or “depends,” including {eta_vague_by_cat['Data Recovery']}/{cat['Data Recovery']} Data Recovery, {eta_vague_by_cat['Hardware Issue']}/{cat['Hardware Issue']} Hardware Issue, and {eta_vague_by_cat['Technical Issue']}/{cat['Technical Issue']} Technical Issue tickets. None of these values is an observed resolution duration or a defensible service commitment. The prior claim of an average 2–3 business days cannot be calculated from this archive.

**A review queue is the next experiment.** Separate incident severity, response target, and resolution forecast; permit an explicit “needs diagnosis” state. Ask human reviewers to label urgency and resolution outcomes on a consented sample, then evaluate agreement, escalation misses, calibration, and subgroup failures before any automated routing. The saved outputs alone cannot establish classification accuracy, response safety, speed at scale, or business impact.

## Evidence boundary

The original notebook displays the first five parsed rows and aggregate tables; it does not retain a complete machine-readable row-level result set or the source dataset. This page only publishes aggregates. Its saved outputs document one historical run of a local GGUF model, with no ground-truth categories, priority labels, actual resolution times, or live follow-up. Counts are descriptive of that run and should not be treated as performance metrics.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the tracked report against the archived outputs")
    args = parser.parse_args()
    report = render(extract())
    if args.check:
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != report:
            raise SystemExit("FINDINGS.md differs from the archived outputs; run analyze.py to rebuild")
        print("PASS: source hash, counts, cross-tabs, and FINDINGS.md reconcile")
    else:
        REPORT.write_text(report, encoding="utf-8", newline="\n")
        print(f"Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
