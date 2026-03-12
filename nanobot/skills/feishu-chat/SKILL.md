---
name: feishu-chat
description: 飞书群组管理 — 列出群组、获取群信息、获取群成员列表
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书群组管理

## 使用流程

1. 阅读 `references/chat.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_chat.py list --limit 20
python3 scripts/feishu_chat.py info --chat-id oc_xxx
python3 scripts/feishu_chat.py members --chat-id oc_xxx --all
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
