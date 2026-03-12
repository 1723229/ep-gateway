---
name: feishu-approval
description: 飞书审批 — 审批定义查询、实例管理、请假审批
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书审批

## 使用流程

1. 阅读 `references/approval.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_approval.py definition --code E565EC28-57C7-461C-B7ED-1E2D838F4878
python3 scripts/feishu_approval.py list --code E565EC28-57C7-461C-B7ED-1E2D838F4878 --limit 20
python3 scripts/feishu_approval.py get --instance-code xxx
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
