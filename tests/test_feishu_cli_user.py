import json
import subprocess

from discord_weekly_report.feishu.cli_user import FeishuCliUserClient


def _completed(payload, returncode=0):
    return subprocess.CompletedProcess(["lark-cli"], returncode, stdout=json.dumps(payload, ensure_ascii=False), stderr="")


def test_cli_user_lists_field_names() -> None:
    def runner(args):
        return _completed({"ok": True, "data": {"fields": [{"name": "帖子链接"}, {"name": "AI短标题"}]}})

    import asyncio

    client = FeishuCliUserClient(cli_path="lark-cli", runner=runner)
    fields = asyncio.run(client.list_table_field_names(app_token="base", table_id="tbl"))

    assert fields == {"帖子链接", "AI短标题"}


def test_cli_user_upsert_uses_record_id_for_existing_link() -> None:
    calls = []

    def runner(args):
        calls.append(args)
        if "+record-list" in args:
            return _completed(
                {
                    "ok": True,
                    "data": {
                        "records": [
                            {
                                "record_id": "rec1",
                                "fields": {"帖子链接": {"text": "查看原帖", "link": "https://discord/post/1"}},
                            }
                        ]
                    },
                }
            )
        return _completed({"ok": True, "data": {"record": {"record_id": "rec1"}}})

    import asyncio

    client = FeishuCliUserClient(cli_path="lark-cli", runner=runner)
    asyncio.run(
        client.upsert_records(
            app_token="base",
            table_id="tbl",
            records=[{"帖子链接": {"text": "查看原帖", "link": "https://discord/post/1"}}],
        )
    )

    upsert_call = calls[-1]
    assert "+record-upsert" in upsert_call
    assert "--record-id" in upsert_call
    assert "rec1" in upsert_call
