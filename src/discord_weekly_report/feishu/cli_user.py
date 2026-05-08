from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from .post_records import POST_DETAIL_FIELDS, _extract_url


CliRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


class FeishuCliUserClient:
    def __init__(self, *, cli_path: str = "", runner: CliRunner | None = None) -> None:
        self.cli_path = cli_path or _default_cli_path()
        self.runner = runner or self._run

    async def auth_status(self) -> dict[str, Any]:
        return await asyncio.to_thread(self._json_command, ["auth", "status"])

    async def require_user_auth(self) -> None:
        status = await self.auth_status()
        identity = status.get("identity")
        token_status = status.get("tokenStatus")
        if identity != "user" or token_status == "expired":
            raise RuntimeError(
                "lark-cli user token is not available. Run `lark-cli auth login` first, "
                "then retry. Current status: "
                f"identity={identity!r}, tokenStatus={token_status!r}."
            )

    async def list_table_field_names(self, *, app_token: str, table_id: str) -> set[str]:
        payload = await asyncio.to_thread(
            self._json_command,
            [
                "base",
                "+field-list",
                "--base-token",
                app_token,
                "--table-id",
                table_id,
                "--as",
                "user",
                "--limit",
                "100",
            ],
        )
        fields = payload.get("data", {}).get("fields", [])
        return {field["name"] for field in fields if isinstance(field, dict) and isinstance(field.get("name"), str)}

    async def list_existing_post_links(self, *, app_token: str, table_id: str) -> dict[str, str]:
        payload = await asyncio.to_thread(
            self._json_command,
            [
                "base",
                "+record-list",
                "--base-token",
                app_token,
                "--table-id",
                table_id,
                "--as",
                "user",
                "--limit",
                "100",
            ],
        )
        records = payload.get("data", {}).get("records") or payload.get("data", {}).get("items") or []
        result: dict[str, str] = {}
        for record in records:
            if not isinstance(record, dict):
                continue
            record_id = record.get("record_id") or record.get("id")
            fields = record.get("fields", {})
            if not isinstance(record_id, str) or not isinstance(fields, dict):
                continue
            url = _extract_url(fields.get("帖子链接"))
            if url:
                result[url] = record_id
        return result

    async def upsert_records(self, *, app_token: str, table_id: str, records: list[dict[str, Any]]) -> None:
        existing_links = await self.list_existing_post_links(app_token=app_token, table_id=table_id)
        for record in records:
            record_id = existing_links.get(_extract_url(record["帖子链接"]))
            await asyncio.to_thread(
                self._upsert_record,
                app_token,
                table_id,
                record,
                record_id,
            )

    def _upsert_record(self, app_token: str, table_id: str, record: dict[str, Any], record_id: str | None) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(record, handle, ensure_ascii=False)
            json_path = handle.name
        try:
            args = [
                "base",
                "+record-upsert",
                "--base-token",
                app_token,
                "--table-id",
                table_id,
                "--as",
                "user",
                "--json",
                f"@{json_path}",
            ]
            if record_id:
                args.extend(["--record-id", record_id])
            self._json_command(args)
        finally:
            Path(json_path).unlink(missing_ok=True)

    def _json_command(self, args: list[str]) -> dict[str, Any]:
        completed = self.runner([self.cli_path, *args])
        if completed.returncode != 0:
            raise RuntimeError(_cli_error(completed))
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"lark-cli returned non-JSON output: {completed.stdout}") from exc
        if payload.get("ok") is False:
            raise RuntimeError(f"lark-cli error: {json.dumps(payload, ensure_ascii=False)}")
        return payload

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


async def validate_cli_user_fields(*, client: FeishuCliUserClient, app_token: str, table_id: str) -> set[str]:
    existing = await client.list_table_field_names(app_token=app_token, table_id=table_id)
    missing = [field for field in POST_DETAIL_FIELDS if field not in existing]
    if missing:
        raise ValueError(f"Feishu Bitable missing required post detail fields: {', '.join(missing)}")
    return existing


def _default_cli_path() -> str:
    npm_bin = Path(os.environ.get("APPDATA", "")) / "npm" / "lark-cli.cmd"
    if npm_bin.exists():
        return str(npm_bin)
    return "lark-cli"


def _cli_error(completed: subprocess.CompletedProcess[str]) -> str:
    output = completed.stderr.strip() or completed.stdout.strip()
    return f"lark-cli failed with exit code {completed.returncode}: {output}"
