---
name: feishu-attendance
description: 飞书考勤 — 查询员工打卡记录
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书考勤

## 使用流程

1. 阅读 `references/attendance.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作
3. 注意：考勤 API 需要 employee_id，可先用通讯录接口获取

## CLI 示例

```bash
python3 scripts/feishu_attendance.py query --user-ids EID001,EID002 --date-from 20260301 --date-to 20260312
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
