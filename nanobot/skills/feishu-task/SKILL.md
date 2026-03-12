---
name: feishu-task
description: 飞书任务管理 — 任务 CRUD、任务清单管理
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书任务管理

## 使用流程

1. 阅读 `references/task.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_task.py list --limit 50
python3 scripts/feishu_task.py get --task-id xxx
python3 scripts/feishu_task.py create --summary "完成报告" --description "Q1季度报告"
python3 scripts/feishu_task.py complete --task-id xxx
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
