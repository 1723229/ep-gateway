---
name: feishu-calendar
description: 飞书日历与日程 — 日历列表、日程 CRUD、忙闲查询、会议室
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书日历与日程

## 使用流程

1. 阅读 `references/calendar.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_calendar.py list
python3 scripts/feishu_calendar.py events --calendar-id primary --limit 50
python3 scripts/feishu_calendar.py create-event --summary "周会" --start-time "2026-03-12T14:00:00+08:00" --end-time "2026-03-12T15:00:00+08:00"
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
