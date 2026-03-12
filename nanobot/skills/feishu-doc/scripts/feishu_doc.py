#!/usr/bin/env python3
"""feishu_doc - 飞书云文档 API

凭据获取优先级: ~/.hiperone/config.json > 环境变量
"""

import argparse
import json
import os
import sys
import time as _time
import requests
from typing import Any, Dict, List, Optional


BASE_URL = "https://open.feishu.cn/open-apis"


def _load_nanobot_config() -> Dict[str, str]:
    config_path = os.path.expanduser("~/.hiperone/config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            feishu = config.get("channels", {}).get("feishu", {})
            if feishu.get("enabled"):
                return {"appId": feishu.get("appId"), "appSecret": feishu.get("appSecret")}
    except Exception:
        pass
    return {}


_nanobot_cfg = _load_nanobot_config()
APP_ID = _nanobot_cfg.get("appId") or os.environ.get("NANOBOT_CHANNELS__FEISHU__APP_ID", "")
APP_SECRET = _nanobot_cfg.get("appSecret") or os.environ.get("NANOBOT_CHANNELS__FEISHU__APP_SECRET", "")
_token_cache: Dict[str, Any] = {"token": "", "expires": 0}


def get_tenant_access_token() -> str:
    if not APP_ID or not APP_SECRET:
        raise RuntimeError(
            "缺少飞书凭据，请配置 ~/.hiperone/config.json 或设置环境变量 "
            "NANOBOT_CHANNELS__FEISHU__APP_ID / NANOBOT_CHANNELS__FEISHU__APP_SECRET"
        )
    now = _time.time()
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 Token 失败: {data}")
    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expires"] = now + data.get("expire", 7200) - 60
    return _token_cache["token"]


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_tenant_access_token()}"}


def _check(data: dict, action: str) -> dict:
    if data.get("code") != 0:
        raise RuntimeError(f"{action}失败: [{data.get('code')}] {data.get('msg', 'Unknown error')}")
    return data.get("data", {})


def _get(path: str, params: Optional[dict] = None, *, timeout: int = 10, action: str = "") -> dict:
    resp = requests.get(f"{BASE_URL}{path}", headers=_headers(), params=params, timeout=timeout)
    return _check(resp.json(), action or path)


def _post(path: str, payload: Optional[dict] = None, *, params: Optional[dict] = None,
          timeout: int = 10, action: str = "") -> dict:
    resp = requests.post(f"{BASE_URL}{path}", headers=_headers(), json=payload,
                         params=params, timeout=timeout)
    return _check(resp.json(), action or path)


def _pp(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ============================================================
# 云文档 (docx/v1, drive/v1)
# ============================================================

def list_files(parent_node: str = "", page_size: int = 20) -> List[Dict]:
    """获取云文档文件列表"""
    params: Dict[str, Any] = {"page_size": page_size}
    if parent_node:
        params["parent_node"] = parent_node
    data = _get("/drive/v1/files", params, action="获取文件列表")
    return data.get("files", [])


def read_doc(document_id: str) -> str:
    """读取云文档内容，返回 Markdown 格式纯文本"""
    params: Dict[str, Any] = {"page_size": 100}
    all_blocks: List[Dict] = []
    while True:
        data = _get(f"/docx/v1/documents/{document_id}/blocks", params, timeout=15,
                     action="获取文档内容")
        all_blocks.extend(data.get("items", []))
        page_token = data.get("page_token")
        if not page_token:
            break
        params = {"page_size": 100, "page_token": page_token}
    return _extract_text_from_blocks(all_blocks)


def search_docs(keyword: str, page_size: int = 10) -> List[Dict]:
    """搜索云文档（使用 suite 搜索 API）"""
    payload = {"search_key": keyword, "count": page_size, "offset": 0, "docs_types": []}
    data = _post("/suite/docs-api/search/object", payload, action="搜索文档")
    return data.get("docs_entities", [])


_BLOCK_TYPE_KEY = {
    2: "paragraph", 3: "heading1", 4: "heading2", 5: "heading3",
    7: "bulleted_list_item", 8: "numbered_list_item", 11: "quote",
}
_BLOCK_TYPE_PREFIX = {3: "## ", 4: "### ", 5: "#### ", 7: "- ", 8: "1. "}


def _extract_text_from_elements(elements: list) -> str:
    parts = []
    for elem in elements:
        if "text_run" in elem:
            parts.append(elem["text_run"].get("content", ""))
        elif "text" in elem:
            parts.append(elem["text"].get("content", ""))
    return "".join(parts)


def _extract_text_from_blocks(blocks: list) -> str:
    text_parts = []
    for block in blocks:
        bt = block.get("block_type")
        if bt == 1:
            continue
        if bt == 10:
            text_parts.append("```\n" + block.get("code", {}).get("content", "") + "\n```")
            continue
        key = _BLOCK_TYPE_KEY.get(bt)
        if not key:
            continue
        elements = block.get(key, {}).get("elements", [])
        text = _extract_text_from_elements(elements)
        if bt == 11:
            text = "\n".join("> " + line for line in text.split("\n"))
        else:
            text = _BLOCK_TYPE_PREFIX.get(bt, "") + text
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)


# ============================================================
# CLI
# ============================================================

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="feishu_doc", description="飞书云文档")
    sub = parser.add_subparsers(dest="action")
    p = sub.add_parser("list", help="列出文件")
    p.add_argument("--parent-node", default="")
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("read", help="读取文档")
    p.add_argument("--document-id", required=True)
    p = sub.add_parser("search", help="搜索文档")
    p.add_argument("--keyword", required=True)
    p.add_argument("--limit", type=int, default=10)
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    act = args.action
    if act == "list":
        _pp(list_files(args.parent_node, args.limit))
    elif act == "read":
        print(read_doc(args.document_id))
    elif act == "search":
        _pp(search_docs(args.keyword, args.limit))


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.action:
        parser.print_help()
        return 1
    try:
        _run_cli(args)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
