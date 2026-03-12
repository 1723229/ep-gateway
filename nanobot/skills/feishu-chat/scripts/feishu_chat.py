#!/usr/bin/env python3
"""feishu_chat - 飞书群组管理 API

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
    """从 nanobot config.json 读取飞书配置"""
    config_path = os.path.expanduser("~/.hiperone/config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            feishu = config.get("channels", {}).get("feishu", {})
            if feishu.get("enabled"):
                return {
                    "appId": feishu.get("appId"),
                    "appSecret": feishu.get("appSecret"),
                }
    except Exception:
        pass
    return {}


_nanobot_cfg = _load_nanobot_config()
APP_ID = _nanobot_cfg.get("appId") or os.environ.get("NANOBOT_CHANNELS__FEISHU__APP_ID", "")
APP_SECRET = _nanobot_cfg.get("appSecret") or os.environ.get("NANOBOT_CHANNELS__FEISHU__APP_SECRET", "")

_token_cache: Dict[str, Any] = {"token": "", "expires": 0}


def get_tenant_access_token() -> str:
    """获取 tenant_access_token（带缓存，有效期内不重复请求）"""
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
# 群组管理 (im/v1/chats)
# ============================================================

def list_chats(page_size: int = 20, page_token: str = "") -> Dict[str, Any]:
    """获取机器人所在的群列表"""
    params: Dict[str, Any] = {"page_size": page_size}
    if page_token:
        params["page_token"] = page_token
    return _get("/im/v1/chats", params, action="获取群列表")


def get_chat(chat_id: str) -> Dict[str, Any]:
    """获取群信息"""
    return _get(f"/im/v1/chats/{chat_id}", action="获取群信息")


def get_chat_members(
    chat_id: str,
    member_id_type: str = "open_id",
    page_size: int = 100,
    page_token: str = "",
) -> Dict[str, Any]:
    """获取群成员列表（单页）"""
    params: Dict[str, Any] = {"member_id_type": member_id_type, "page_size": page_size}
    if page_token:
        params["page_token"] = page_token
    return _get(f"/im/v1/chats/{chat_id}/members", params, action="获取群成员列表")


def get_chat_members_all(chat_id: str, member_id_type: str = "open_id") -> List[Dict]:
    """获取群全部成员（自动分页）"""
    members: List[Dict] = []
    page_token = ""
    while True:
        data = get_chat_members(chat_id, member_id_type, page_size=100, page_token=page_token)
        members.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
    return members


# ============================================================
# CLI
# ============================================================

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="feishu_chat", description="飞书群组管理")
    sub = parser.add_subparsers(dest="action")
    p = sub.add_parser("list", help="列出群组")
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("info", help="获取群信息")
    p.add_argument("--chat-id", required=True)
    p = sub.add_parser("members", help="获取群成员")
    p.add_argument("--chat-id", required=True)
    p.add_argument("--all", action="store_true")
    p.add_argument("--limit", type=int, default=100)
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    act = args.action
    if act == "list":
        _pp(list_chats(args.limit))
    elif act == "info":
        _pp(get_chat(args.chat_id))
    elif act == "members":
        if args.all:
            _pp(get_chat_members_all(args.chat_id))
        else:
            _pp(get_chat_members(args.chat_id, page_size=args.limit))


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
