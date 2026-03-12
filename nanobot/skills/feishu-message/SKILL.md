---
name: feishu-message
description: 飞书消息收发 — 发送/回复/获取消息、会话历史
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书消息收发

## 使用流程

1. 阅读 `references/message.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_message.py history --chat-id oc_xxx --limit 20
python3 scripts/feishu_message.py send --receive-id oc_xxx --text "Hello"
python3 scripts/feishu_message.py get --message-id om_xxx
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
