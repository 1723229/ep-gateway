---
name: feishu-bitable
description: 飞书多维表格 — 数据表 CRUD、日报录入、任务管理
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书多维表格

## 使用流程

1. 阅读 `references/bitable.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_bitable.py tables --app-token JXdtbkkchaSXmksx6eFc2Eatn45
python3 scripts/feishu_bitable.py fields --app-token TOKEN --table-id tblXXX
python3 scripts/feishu_bitable.py list --app-token TOKEN --table-id tblXXX --limit 20
python3 scripts/feishu_bitable.py daily-query --limit 10
python3 scripts/feishu_bitable.py task-query --limit 10
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
