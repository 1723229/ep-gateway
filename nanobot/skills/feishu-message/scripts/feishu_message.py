#!/usr/bin/env python3
"""feishu_message - 飞书消息收发 API

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
# 消息 (im/v1/messages)
# ============================================================

def get_chat_history(
    chat_id: str,
    start_time: str = "",
    end_time: str = "",
    page_size: int = 20,
    page_token: str = "",
) -> Dict[str, Any]:
    """获取会话历史消息"""
    params: Dict[str, Any] = {
        "container_id_type": "chat",
        "container_id": chat_id,
        "page_size": min(page_size, 50),
    }
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    if page_token:
        params["page_token"] = page_token
    return _get("/im/v1/messages", params, action="获取会话历史消息")


def send_message(
    receive_id: str,
    msg_type: str,
    content: str,
    receive_id_type: str = "chat_id",
) -> Dict[str, Any]:
    """发送消息"""
    payload = {"receive_id": receive_id, "msg_type": msg_type, "content": content}
    return _post("/im/v1/messages", payload, params={"receive_id_type": receive_id_type},
                 action="发送消息")


def send_text(receive_id: str, text: str, receive_id_type: str = "chat_id") -> Dict[str, Any]:
    """发送文本消息（便捷函数）"""
    return send_message(receive_id, "text", json.dumps({"text": text}), receive_id_type)


def reply_message(message_id: str, msg_type: str, content: str) -> Dict[str, Any]:
    """回复消息"""
    return _post(f"/im/v1/messages/{message_id}/reply",
                 {"msg_type": msg_type, "content": content}, action="回复消息")


def get_message(message_id: str) -> Dict[str, Any]:
    """获取单条消息"""
    return _get(f"/im/v1/messages/{message_id}", action="获取消息")


# ============================================================
# CLI
# ============================================================

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="feishu_message", description="飞书消息收发")
    sub = parser.add_subparsers(dest="action")
    p = sub.add_parser("history", help="会话历史")
    p.add_argument("--chat-id", required=True)
    p.add_argument("--start-time", default="")
    p.add_argument("--end-time", default="")
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("send", help="发送文本")
    p.add_argument("--receive-id", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--id-type", default="chat_id")
    p = sub.add_parser("get", help="获取单条消息")
    p.add_argument("--message-id", required=True)
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    act = args.action
    if act == "history":
        _pp(get_chat_history(args.chat_id, args.start_time, args.end_time, args.limit))
    elif act == "send":
        _pp(send_text(args.receive_id, args.text, args.id_type))
    elif act == "get":
        _pp(get_message(args.message_id))


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
