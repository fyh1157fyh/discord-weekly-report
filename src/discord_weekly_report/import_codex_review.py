from __future__ import annotations

import asyncio
import json

from .codex_review import apply_codex_review, codex_review_path
from .config import Settings
from .date_range import previous_full_week
from .feishu.publisher import publish_weekly_posts
from .paths import ensure_output_paths
from .report_io import load_weekly_report
from .report_writer import write_outputs


async def _run() -> None:
    settings = Settings.from_env(require_sources=False, require_discord_token=False)
    week = previous_full_week(timezone=settings.timezone)
    paths = ensure_output_paths(settings.output_dir, week.label)
    report = load_weekly_report(paths.analyzed_json)
    review_path = codex_review_path(paths.analyzed_json)
    review_data = json.loads(review_path.read_text(encoding="utf-8"))
    reviewed_report = apply_codex_review(report, review_data)
    raw_posts = [item.post for item in reviewed_report.posts]
    write_outputs(paths, raw_posts, reviewed_report)
    print(f"Imported Codex review: {review_path}")
    print(f"Updated local report: {paths.markdown}")
    if settings.enable_feishu:
        await publish_weekly_posts(settings=settings, report=reviewed_report, markdown_path=paths.markdown)
        print("Updated Feishu post detail records.")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
