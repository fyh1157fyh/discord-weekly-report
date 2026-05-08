from __future__ import annotations

from .codex_review import codex_review_path, render_codex_review_input, write_review_json_template
from .config import Settings
from .date_range import previous_full_week
from .paths import ensure_output_paths
from .report_io import load_weekly_report


def main() -> None:
    settings = Settings.from_env(require_sources=False, require_discord_token=False)
    week = previous_full_week(timezone=settings.timezone)
    paths = ensure_output_paths(settings.output_dir, week.label)
    report = load_weekly_report(paths.analyzed_json)
    paths.codex_input.write_text(render_codex_review_input(report), encoding="utf-8")
    review_path = codex_review_path(paths.analyzed_json)
    write_review_json_template(review_path, report)
    print(f"Codex review input written: {paths.codex_input}")
    print(f"Codex review JSON template written: {review_path}")


if __name__ == "__main__":
    main()
