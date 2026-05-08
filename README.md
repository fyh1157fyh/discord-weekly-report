# Discord Weekly Report

每周采集 Discord 玩家建议，生成本地 Markdown 周报，并可写入飞书多维表格的帖子级明细表。

## Quick Start

```powershell
cd D:\Codex-Standalone-tasks\discord-weekly-report
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
copy .env.example .env
```

填好 `.env` 后运行：

```powershell
.\.venv\Scripts\python.exe -m discord_weekly_report.main
```

## Feishu

先验证多维表格字段和写入权限：

```powershell
.\.venv\Scripts\python.exe -m discord_weekly_report.verify_feishu
```

只验证飞书消息：

```powershell
.\.venv\Scripts\python.exe -m discord_weekly_report.verify_feishu_message
```

飞书主表需要这些字段：

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

程序使用 `帖子链接` 去重：已存在则更新，不存在则新增。

## AI Analysis

默认使用本地规则生成中文标题和总结。如果想让标题更像“商店增加燃油”“联盟排行显示零贡献成员”这种具体问题概括，可以在 `.env` 开启 OpenAI 兼容接口：

```env
ENABLE_AI_ANALYSIS=1
AI_API_KEY=你的 AI Key
AI_BASE_URL=https://你的接口地址/v1
AI_MODEL=你的模型名
AI_BATCH_SIZE=20
```

AI 失败时会自动回退到本地规则，不会影响本地报告或飞书写表。

## Codex Local Review

如果不想接外部 AI API，可以使用 Codex 本地精修流程：

```powershell
.\.venv\Scripts\python.exe -m discord_weekly_report.prepare_codex_review
```

这个命令会生成：

```text
data/analyzed/YYYY-Www.codex-input.md
data/analyzed/YYYY-Www.codex-review.json
```

让 Codex 读取 `codex-input.md`，把整理后的 JSON 写入 `codex-review.json`，再运行：

```powershell
.\.venv\Scripts\python.exe -m discord_weekly_report.import_codex_review
```

导入后会更新本地 Markdown/JSON；如果 `ENABLE_FEISHU=1`，还会同步更新飞书多维表格。

## Topics

专题关键词统一配置在 `config/topics.yml`。

```env
ACTIVE_TOPIC_KEYS=all
```

设置为 `all` 会启用 `topics.yml` 里的全部专题。只想跑部分专题时，再写成 `arena,trunk` 这种逗号分隔格式。
