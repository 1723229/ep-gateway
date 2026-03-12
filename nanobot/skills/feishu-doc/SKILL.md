---
name: feishu-doc
description: 飞书云文档 — 文件列表、读取文档内容、搜索文档
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书云文档

## 使用流程

1. 阅读 `references/doc.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_doc.py list --limit 20
python3 scripts/feishu_doc.py read --document-id doxcnXXX
python3 scripts/feishu_doc.py search --keyword "季度报告"
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
