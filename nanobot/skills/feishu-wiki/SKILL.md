---
name: feishu-wiki
description: 飞书知识库 — 知识空间列表、节点管理、搜索
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书知识库

## 使用流程

1. 阅读 `references/wiki.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_wiki.py spaces
python3 scripts/feishu_wiki.py nodes --space-id xxx
python3 scripts/feishu_wiki.py search --keyword "技术文档"
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
