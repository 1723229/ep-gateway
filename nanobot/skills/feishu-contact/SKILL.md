---
name: feishu-contact
description: 飞书通讯录 — 用户信息查询、部门与子部门列表
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书通讯录

## 使用流程

1. 阅读 `references/contact.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_contact.py user --user-id ou_xxx
python3 scripts/feishu_contact.py dept-users --department-id 0 --limit 50
python3 scripts/feishu_contact.py dept --department-id od_xxx
python3 scripts/feishu_contact.py dept-children --parent-id 0
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
