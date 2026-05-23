"""xhs-pipeline Hermes plugin — 包装 huitun_collect.py 的 3 个采集源.

设计哲学（ADR-015 agent-first）:
- 3 个 tool 各自是「单一原子能力」, 不写 end-to-end pipeline
- agent 根据 goal 自主决定调用哪个 / 哪几个 / 什么顺序
- check_fn 只看 session 文件是否存在; 缺 session 时 tool 仍注册（在 `hermes tools` 可见）
  但 dispatch 时会被门控
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from tools.registry import tool_error, tool_result


# ============================================================
# 路径常量
# ============================================================
PLUGIN_DIR = Path(__file__).parent
HUITUN_SCRIPT = PLUGIN_DIR / "huitun_collect.py"
SESSION_FILE = PLUGIN_DIR / "tools" / "huitun_session.json"
DEFAULT_OUTPUT_DIR = PLUGIN_DIR / "outputs"

# huitun_collect.py 用 Playwright + chromium, 不能用 hermes venv 的 python
# （hermes venv 装的依赖跟 xhs-content-pipeline 自己的 requirements-collect.txt 不一致）
# 用系统 python（用户已装好 playwright + chromium）
_SYSTEM_PYTHON = sys.executable  # 默认跟 hermes 走; 用户可通过 env var override


# ============================================================
# check_fn
# ============================================================
def _check_huitun_available() -> bool:
    """灰豚 session 文件存在 = 用户已经跑过 huitun_collect.py login."""
    return SESSION_FILE.exists()


# ============================================================
# 工具函数
# ============================================================
def _run_huitun_subcmd(subcmd: str, extra_args: list[str], timeout_sec: int = 600) -> dict:
    """统一调用 huitun_collect.py 子命令, 返回解析好的 JSON dict.

    抛 RuntimeError 让 handler 把它转成 tool_error.
    """
    if not HUITUN_SCRIPT.exists():
        raise RuntimeError(f"huitun_collect.py 不存在: {HUITUN_SCRIPT}")

    # 输出路径: 每次调用生成一个时间戳文件, 避免覆盖
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DEFAULT_OUTPUT_DIR / f"{subcmd}_{int(time.time())}.json"

    cmd = [
        _SYSTEM_PYTHON,
        str(HUITUN_SCRIPT),
        subcmd,
        "--output", str(output_path),
        "--headless",  # plugin 调用强制 headless（不弹窗扰用户）
        *extra_args,
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"huitun {subcmd} 超时 ({timeout_sec}s)")

    if proc.returncode != 0:
        stderr_tail = (proc.stderr or "").strip().splitlines()[-10:]
        raise RuntimeError(
            f"huitun {subcmd} 失败 (exit={proc.returncode}). stderr 最后 10 行:\n"
            + "\n".join(stderr_tail)
        )

    if not output_path.exists():
        raise RuntimeError(f"huitun {subcmd} 没产出 output: {output_path}")

    try:
        return json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"huitun {subcmd} output JSON 解析失败: {e}")


def _summarize_for_agent(payload: dict, max_notes: int = 20) -> dict:
    """裁剪 output, 避免 agent context 撑爆.

    保留: meta + stats + 前 N 条笔记的关键字段
    丢弃: 长字段（封面 URL list, 二维码 base64, 原始 DOM 等）

    字段映射依据 huitun_collect.py:378-410 的扁平结构.
    """
    notes = payload.get("notes", [])
    trimmed_notes = []
    for n in notes[:max_notes]:
        author_raw = n.get("author")
        if isinstance(author_raw, dict):
            author = {
                "name": author_raw.get("name"),
                "followers": author_raw.get("followers"),
                "level": author_raw.get("level"),
            }
        else:
            author = author_raw

        # 注意 URL 字段优先级:
        # 1. raw_xhs_url - huitun 抓回的带 xsec_token 完整 URL（小红书登录态下可访问）
        # 2. real_xhs_url - 兼容旧字段名（如果某天 huitun_collect.py 改字段）
        # 3. url - 不带 token 的 explore/<id>（小红书 300031 登录墙会拒）
        # xhs_extract_note 必须用带 token 的 URL 才能通过登录墙
        trimmed_notes.append({
            "title": n.get("title"),
            "author": author,
            "real_xhs_url": n.get("raw_xhs_url") or n.get("real_xhs_url") or n.get("url"),
            "note_type": n.get("note_type"),
            "likes": n.get("likes"),
            "collects": n.get("collects"),
            "comments": n.get("comments"),
            "shares": n.get("shares"),
            "total_interaction": n.get("total_interaction"),
            "ces_partial": n.get("ces_partial"),
            "predicted_read": n.get("predicted_read"),
            "publish_date": n.get("publish_date"),
            "note_id": n.get("note_id") or n.get("row_key"),
        })

    return {
        "collected_at": payload.get("collected_at"),
        "source": payload.get("source"),
        "query": payload.get("query"),
        "stats": payload.get("stats"),
        "notes_preview_count": len(trimmed_notes),
        "notes_total_in_file": len(notes),
        "notes": trimmed_notes,
        "output_file_hint": "完整数据在 outputs 目录的 JSON 文件里，agent 需要更多字段时可读文件",
    }


# ============================================================
# Tool: huitun_search (A 路线 - 品类关键词搜索)
# ============================================================
HUITUN_SEARCH_SCHEMA = {
    "name": "huitun_search",
    "description": (
        "A 路线: 灰豚按赛道关键词搜小红书爆款笔记。"
        "用于「我要找 X 品类近 7 天的爆款做拆解」场景。"
        "需要先在终端跑 `python huitun_collect.py login` 保存灰豚 session。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "niche": {
                "type": "string",
                "description": "赛道关键词，逗号分隔（如 '字节设计面试,腾讯设计岗'）。不传则用路飞场景默认清单。",
            },
            "date_range": {
                "type": "string",
                "enum": ["1d", "3d", "7d", "30d"],
                "description": "时间范围，默认 7d",
            },
            "top": {
                "type": "integer",
                "description": "采集 top N 条，默认 30，上限 50（反爬）",
            },
        },
        "required": [],
    },
}


def _handle_huitun_search(args: dict, **kw) -> str:
    try:
        extra = []
        if args.get("niche"):
            extra += ["--niche", str(args["niche"])]
        if args.get("date_range"):
            extra += ["--date-range", str(args["date_range"])]
        if args.get("top"):
            extra += ["--top", str(args["top"])]

        payload = _run_huitun_subcmd("search", extra)
        return tool_result(_summarize_for_agent(payload))
    except Exception as e:
        return tool_error(f"huitun_search 失败: {type(e).__name__}: {e}")


# ============================================================
# Tool: huitun_hot (B 路线 - 笔记榜单)
# ============================================================
HUITUN_HOT_SCHEMA = {
    "name": "huitun_hot",
    "description": (
        "B 路线: 灰豚「笔记榜单」抓全网热点头部笔记（不限品类）。"
        "用于「这周全网什么内容在爆」场景, 找跨赛道借鉴。"
        "需要先跑 login 保存 session。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "top": {
                "type": "integer",
                "description": "采集 top N 条，默认 30，上限 50",
            },
        },
        "required": [],
    },
}


def _handle_huitun_hot(args: dict, **kw) -> str:
    try:
        extra = []
        if args.get("top"):
            extra += ["--top", str(args["top"])]

        payload = _run_huitun_subcmd("hot", extra)
        return tool_result(_summarize_for_agent(payload))
    except Exception as e:
        return tool_error(f"huitun_hot 失败: {type(e).__name__}: {e}")


# ============================================================
# Tool: huitun_collect_my (C 路线 - 我的收藏)
# ============================================================
HUITUN_COLLECT_MY_SCHEMA = {
    "name": "huitun_collect_my",
    "description": (
        "C 路线: 抓灰豚账号「我的收藏」里手动收藏过的笔记。"
        "用于「我自己挑了几条想拆的, 把元数据拉下来」场景, 完全人工筛选不依赖算法。"
        "需要先跑 login 保存 session, 并在灰豚前端手动收藏过笔记。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "top": {
                "type": "integer",
                "description": "采集 top N 条，默认 50，上限 50",
            },
        },
        "required": [],
    },
}


def _handle_huitun_collect_my(args: dict, **kw) -> str:
    try:
        extra = []
        if args.get("top"):
            extra += ["--top", str(args["top"])]

        payload = _run_huitun_subcmd("my_collect", extra)
        return tool_result(_summarize_for_agent(payload))
    except Exception as e:
        return tool_error(f"huitun_collect_my 失败: {type(e).__name__}: {e}")


# ============================================================
# 注册入口（hermes plugin loader 调）
# ============================================================
_TOOLS = (
    ("huitun_search",     HUITUN_SEARCH_SCHEMA,     _handle_huitun_search,     "🔎"),
    ("huitun_hot",        HUITUN_HOT_SCHEMA,        _handle_huitun_hot,        "🔥"),
    ("huitun_collect_my", HUITUN_COLLECT_MY_SCHEMA, _handle_huitun_collect_my, "📌"),
)


def register(ctx) -> None:
    """plugin 入口, hermes loader 启动时调一次."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="xhs",
            schema=schema,
            handler=handler,
            check_fn=_check_huitun_available,
            emoji=emoji,
        )
