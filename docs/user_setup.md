# User Setup Guide

This guide is for someone who wants to run the Discord weekly report with their own Discord server and Feishu Bitable.

## 1. Install

Requirements:

- Windows PowerShell
- Python 3.12
- A Discord bot token
- A Feishu app with Bitable permissions

Clone the repo and run setup:

```powershell
git clone https://github.com/fyh1157fyh/discord-weekly-report.git
cd discord-weekly-report
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

The setup script creates `.venv`, installs dependencies, and creates `.env` from `.env.example`.

This project does not require a GitHub Release. It is a Python script project, so cloning the repository is enough.

## 2. Configure Discord

Fill these values in `.env`:

```env
DISCORD_BOT_TOKEN=
DISCORD_GUILD_ID=
DISCORD_FORUM_CHANNEL_IDS=
DISCORD_THREAD_CHANNEL_IDS=
DISCORD_TEXT_CHANNEL_IDS=
DISCORD_MESSAGE_CONTENT_INTENT=1
```

Notes:

- `DISCORD_BOT_TOKEN` is the bot token, not the application ID, public key, or client secret.
- `DISCORD_GUILD_ID` is the server ID.
- `DISCORD_FORUM_CHANNEL_IDS` is for Discord Forum channels.
- `DISCORD_THREAD_CHANNEL_IDS` is for text channels whose threads should be collected.
- `DISCORD_TEXT_CHANNEL_IDS` is for normal chat channels used by topic sentiment matching.
- Multiple channel IDs use commas, for example `111,222,333`.

The bot needs at least:

- View Channels
- Read Message History
- Message Content Intent enabled in the Discord Developer Portal

## 3. Configure Topics

Topic keywords are in:

```text
config/topics.yml
```

To enable all topics:

```env
ACTIVE_TOPIC_KEYS=all
```

To enable only some topics:

```env
ACTIVE_TOPIC_KEYS=arena,migration
```

## 4. Configure Feishu

If you only want local Markdown/JSON output, keep:

```env
ENABLE_FEISHU=0
```

To write Feishu Bitable records, fill:

```env
ENABLE_FEISHU=1
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_BITABLE_APP_TOKEN=
FEISHU_BITABLE_TABLE_ID=
```

The target Bitable must contain these fields:

```text
AI短标题
帖子链接
模块分类
二级分类
状态
满意度
热度分
回复数
AI核心总结
日期
具体建议
参与人数
```

Verify Feishu before running the weekly report:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_feishu.ps1
```

## 5. Run

Run the weekly report:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_weekly.ps1
```

Outputs are written under:

```text
data/raw/
data/analyzed/
data/topics/
reports/
reports/topics/
```

These generated files are ignored by git.

## 6. Codex Local Review

If you do not want to use an external AI API, use Codex to refine the generated summaries:

```powershell
.\.venv\Scripts\python.exe -m discord_weekly_report.prepare_codex_review
```

Ask Codex to refine:

```text
Use the discord-weekly-report skill. Refine this week's codex-input and write it back to Feishu.
```

Then import the refined JSON:

```powershell
.\.venv\Scripts\python.exe -m discord_weekly_report.import_codex_review
```

## 7. Troubleshooting

- `Missing required environment variables`: fill `.env`.
- `invalid literal for int()`: a channel ID field contains a topic name; put topic names in `ACTIVE_TOPIC_KEYS`.
- Discord returns empty content: enable Message Content Intent and check channel permissions.
- Feishu field check fails: create the missing Bitable fields with the exact Chinese names.
- PowerShell blocks scripts: use `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`.
