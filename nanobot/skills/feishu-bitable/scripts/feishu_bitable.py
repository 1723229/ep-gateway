#!/usr/bin/env python3
"""feishu_bitable - 飞书多维表格 API

凭据获取优先级: ~/.hiperone/config.json > 环境变量
"""

import argparse
import json
import os
import sys
import time as _time
import requests
from datetime import datetime, timedelta
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


def _put(path: str, payload: Optional[dict] = None, *, timeout: int = 10, action: str = "") -> dict:
    resp = requests.put(f"{BASE_URL}{path}", headers=_headers(), json=payload, timeout=timeout)
    return _check(resp.json(), action or path)


def _delete(path: str, *, timeout: int = 10, action: str = "") -> dict:
    resp = requests.delete(f"{BASE_URL}{path}", headers=_headers(), timeout=timeout)
    return _check(resp.json(), action or path)


def _pp(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ============================================================
# 多维表格 (bitable/v1)
# ============================================================

def bitable_get_fields(app_token: str, table_id: str) -> Dict[str, Any]:
    """获取多维表格字段定义"""
    return _get(f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                action="获取表字段定义")


def bitable_list_records(
    app_token: str,
    table_id: str,
    page_size: int = 20,
    filter_expr: Optional[str] = None,
    page_token: str = "",
) -> Dict[str, Any]:
    """查询多维表格记录"""
    params: Dict[str, Any] = {"page_size": page_size}
    if filter_expr:
        params["filter"] = filter_expr
    if page_token:
        params["page_token"] = page_token
    return _get(f"/bitable/v1/apps/{app_token}/tables/{table_id}/records", params,
                action="查询多维表格记录")


def bitable_add_record(app_token: str, table_id: str, fields: dict) -> Dict[str, Any]:
    """创建多维表格记录"""
    return _post(f"/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                 {"fields": fields}, action="创建多维表格记录")


def bitable_update_record(
    app_token: str, table_id: str, record_id: str, fields: dict,
) -> Dict[str, Any]:
    """更新多维表格记录"""
    return _put(f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                {"fields": fields}, action="更新多维表格记录")


def bitable_delete_record(app_token: str, table_id: str, record_id: str) -> Dict[str, Any]:
    """删除多维表格记录"""
    return _delete(f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                   action="删除多维表格记录")


def bitable_list_tables(app_token: str, page_size: int = 20) -> Dict[str, Any]:
    """获取多维表格中的数据表列表"""
    return _get(f"/bitable/v1/apps/{app_token}/tables", {"page_size": page_size},
                action="获取数据表列表")


# --- 多维表格预置常量（团队表格） ---
BITABLE_APP_TOKEN = "JXdtbkkchaSXmksx6eFc2Eatn45"
DAILY_TABLE_ID = "tblYWOnDxGsVSfDN"
TASK_TABLE_ID = "tblH6xn2dp6E1UtD"
PROJECT_TABLE_ID = "tblihZwJnOg84PUQ"


def bitable_add_daily_report(
    user_id: str, date: str, project: str, content: str, hours: float,
    app_token: str = BITABLE_APP_TOKEN,
) -> Dict[str, Any]:
    """录入日报"""
    fields = {
        "姓名": [{"id": user_id}],
        "日期": date,
        "项目": project,
        "工作内容": content,
        "时长": str(hours),
    }
    return bitable_add_record(app_token, DAILY_TABLE_ID, fields)


def bitable_query_daily_reports(
    page_size: int = 20, app_token: str = BITABLE_APP_TOKEN,
) -> Dict[str, Any]:
    """查询日报记录"""
    return bitable_list_records(app_token, DAILY_TABLE_ID, page_size=page_size)


def bitable_add_task(
    task_name: str,
    serial_number: int,
    project_record_id: str,
    executor_id: str,
    status: str = "进行中",
    deadline_days: int = 7,
    estimated_hours: int = 2,
    description: str = "",
    table_id: str = TASK_TABLE_ID,
    app_token: str = BITABLE_APP_TOKEN,
) -> Dict[str, Any]:
    """录入任务（自动检测状态字段类型）"""
    fields_info = bitable_get_fields(app_token, table_id)
    status_field_type = None
    for f in fields_info.get("items", []):
        if f.get("field_name") == "状态":
            status_field_type = f.get("type")
            break
    status_value: Any = [status] if status_field_type == 4 else status
    deadline = int((datetime.now() + timedelta(days=deadline_days)).timestamp() * 1000)
    fields = {
        "任务名称": task_name,
        "序号": serial_number,
        "所属项目": [project_record_id],
        "执行人": [{"id": executor_id}],
        "状态": status_value,
        "计划截止时间": deadline,
        "预计耗时": estimated_hours,
        "说明": description,
    }
    return bitable_add_record(app_token, table_id, fields)


def bitable_query_tasks(
    page_size: int = 20,
    table_id: str = TASK_TABLE_ID,
    app_token: str = BITABLE_APP_TOKEN,
) -> Dict[str, Any]:
    """查询任务记录"""
    return bitable_list_records(app_token, table_id, page_size=page_size)


# ============================================================
# CLI
# ============================================================

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="feishu_bitable", description="飞书多维表格")
    sub = parser.add_subparsers(dest="action")
    p = sub.add_parser("tables", help="列出数据表")
    p.add_argument("--app-token", required=True)
    p = sub.add_parser("fields", help="获取字段定义")
    p.add_argument("--app-token", required=True)
    p.add_argument("--table-id", required=True)
    p = sub.add_parser("list", help="查询记录")
    p.add_argument("--app-token", required=True)
    p.add_argument("--table-id", required=True)
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("add", help="创建记录")
    p.add_argument("--app-token", required=True)
    p.add_argument("--table-id", required=True)
    p.add_argument("--fields", required=True, help="字段 JSON")
    p = sub.add_parser("update", help="更新记录")
    p.add_argument("--app-token", required=True)
    p.add_argument("--table-id", required=True)
    p.add_argument("--record-id", required=True)
    p.add_argument("--fields", required=True, help="字段 JSON")
    p = sub.add_parser("delete", help="删除记录")
    p.add_argument("--app-token", required=True)
    p.add_argument("--table-id", required=True)
    p.add_argument("--record-id", required=True)
    p = sub.add_parser("daily-add", help="录入日报")
    p.add_argument("--user-id", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--hours", type=float, required=True)
    p = sub.add_parser("daily-query", help="查询日报")
    p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("task-add", help="录入任务")
    p.add_argument("--name", required=True)
    p.add_argument("--serial", type=int, required=True)
    p.add_argument("--project", required=True, help="项目 record_id")
    p.add_argument("--executor", required=True, help="执行人 open_id")
    p.add_argument("--status", default="进行中")
    p.add_argument("--deadline", type=int, default=7)
    p.add_argument("--hours", type=int, default=2)
    p.add_argument("--description", default="")
    p.add_argument("--table", default=TASK_TABLE_ID)
    p = sub.add_parser("task-query", help="查询任务")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--table", default=TASK_TABLE_ID)
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    act = args.action
    if act == "tables":
        _pp(bitable_list_tables(args.app_token))
    elif act == "fields":
        _pp(bitable_get_fields(args.app_token, args.table_id))
    elif act == "list":
        _pp(bitable_list_records(args.app_token, args.table_id, args.limit))
    elif act == "add":
        _pp(bitable_add_record(args.app_token, args.table_id, json.loads(args.fields)))
    elif act == "update":
        _pp(bitable_update_record(args.app_token, args.table_id, args.record_id,
                                  json.loads(args.fields)))
    elif act == "delete":
        _pp(bitable_delete_record(args.app_token, args.table_id, args.record_id))
    elif act == "daily-add":
        _pp(bitable_add_daily_report(args.user_id, args.date, args.project,
                                     args.content, args.hours))
    elif act == "daily-query":
        _pp(bitable_query_daily_reports(args.limit))
    elif act == "task-add":
        _pp(bitable_add_task(args.name, args.serial, args.project, args.executor,
                             args.status, args.deadline, args.hours, args.description,
                             args.table))
    elif act == "task-query":
        _pp(bitable_query_tasks(args.limit, args.table))


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
