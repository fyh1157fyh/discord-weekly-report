# Setup

1. 安装 Python 3.12。
2. 进入 `D:\Codex-Standalone-tasks\discord-weekly-report` 创建 `.venv` 并安装依赖。
3. 从 `.env.example` 复制 `.env`，填写 Discord 和飞书配置。
4. Discord 机器人需要 `查看频道`、`阅读消息历史`，并在开发者后台开启 `Message Content Intent`。
5. 飞书应用需要 tenant 级多维表格字段读取、记录读取、新增、更新权限。
6. 如需更高质量中文概括，配置 `ENABLE_AI_ANALYSIS=1`、`AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL`。
7. 如果不用外部 AI，则运行 `prepare_codex_review` 生成输入包，让 Codex 精修后再运行 `import_codex_review` 导入结果。

本阶段主落库表是帖子级明细表，不再是问题组汇总表。专题问题组仍用于 Markdown 周报和后续卡片摘要。
