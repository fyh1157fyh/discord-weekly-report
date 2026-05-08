from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OutputPaths:
    raw_json: Path
    analyzed_json: Path
    markdown: Path
    codex_input: Path
    topics_data_dir: Path
    topics_reports_dir: Path


def ensure_output_paths(root: Path, week_label: str) -> OutputPaths:
    raw_dir = root / "data" / "raw"
    analyzed_dir = root / "data" / "analyzed"
    reports_dir = root / "reports"
    topics_data_dir = root / "data" / "topics"
    topics_reports_dir = root / "reports" / "topics"
    for path in [raw_dir, analyzed_dir, reports_dir, topics_data_dir, topics_reports_dir]:
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        raw_json=raw_dir / f"{week_label}.raw.json",
        analyzed_json=analyzed_dir / f"{week_label}.analysis.json",
        markdown=reports_dir / f"{week_label}.md",
        codex_input=analyzed_dir / f"{week_label}.codex-input.md",
        topics_data_dir=topics_data_dir,
        topics_reports_dir=topics_reports_dir,
    )
