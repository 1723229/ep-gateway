---
name: feishu-drive
description: 飞书云空间/文件管理 — 文件夹创建、上传/下载、权限管理
metadata:
  requires:
    - type: binary
      name: python3
---

# 飞书云空间/文件管理

## 使用流程

1. 阅读 `references/drive.md` 获取函数签名和参数说明
2. 通过 `exec` 工具调用脚本执行操作

## CLI 示例

```bash
python3 scripts/feishu_drive.py mkdir --name "项目文件夹"
python3 scripts/feishu_drive.py upload --file /path/to/file.pdf --parent-node folderToken
python3 scripts/feishu_drive.py download --file-token xxx --save-path /tmp/file.pdf
```

## 凭据

自动读取 `~/.hiperone/config.json` 或环境变量 `NANOBOT_CHANNELS__FEISHU__APP_ID` / `NANOBOT_CHANNELS__FEISHU__APP_SECRET`，无需手动配置。
