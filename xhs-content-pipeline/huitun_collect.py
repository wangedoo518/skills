#!/usr/bin/env python3
"""
huitun_collect.py - 灰豚数据小红书爆款采集（Phase 4.4 step 1: 采集）

按 ADR-015 Agent-first 原则：本脚本是单一原子能力（"从灰豚抓小红书爆款元数据"），
不做后续处理（不调 SKILL、不下载视频）。提取由 boss 的 xhs_extract_note 工具完成。

输出 JSON 直接喂给 boss 的 xhs_extract_note 做第二步「提取」。

链路位置：
    采集 (本脚本) → 提取 (boss xhs_extract_note) → 分析 (xhs-viral-analysis) → 表达 (xhs-script-generation)

用法：
    # 一次性：保存灰豚登录态（启动 Playwright，用户手动登，脚本保存 session）
    python huitun_collect.py login

    # 开发用：交互式探索灰豚 UI（让 Claude/dev 看 DOM 结构选 selector）
    python huitun_collect.py explore

    # 采集（用默认赛道关键词清单，针对路飞场景）
    python huitun_collect.py search --top 30 -o ./outputs/notes_20260521.json

    # 采集（指定关键词）
    python huitun_collect.py search --niche "字节面试,腾讯设计岗" --top 50 -o ./outputs/notes.json

依赖：
    pip install -r requirements-collect.txt
    playwright install chromium

反爬规避（内置）：
    - 串行抓取（不并发）
    - 每个动作随机延迟 1-3 秒
    - 单次会话上限 50 条（防止异常请求频率）
    - 失败后 backoff 30 秒重试，最多 3 次
    - 复用 session.json（不每次登）
    - Headless 默认 False（首跑显示浏览器，证明是真人操作模式）
"""
import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def _require_playwright():
    """延迟 import playwright，让 --help 即使没装也能看。"""
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        sys.stderr.write(
            "Error: 缺少 playwright，运行：\n"
            "  pip install -r requirements-collect.txt\n"
            "  playwright install chromium\n"
        )
        sys.exit(1)


# 配置常量
PROJECT_DIR = Path(__file__).parent
SESSION_FILE = PROJECT_DIR / "tools" / "huitun_session.json"  # gitignored
HUITUN_BASE = "https://www.huitun.com"  # TODO 待 explore 阶段确认正确入口 URL

# 路飞场景默认赛道关键词（Phase 4.4 设计原则：只覆盖路飞，不做通用）
DEFAULT_NICHE_KEYWORDS = [
    "设计师求职",
    "字节设计面试",
    "腾讯设计岗",
    "美团设计岗",
    "UX 设计师作品集",
    "UI 设计师面试",
    "大厂设计 offer",
    "交互设计求职",
]

# 反爬常量
DELAY_MIN_SEC = 1.0
DELAY_MAX_SEC = 3.0
MAX_NOTES_PER_SESSION = 50
RETRY_BACKOFF_SEC = 30
MAX_RETRIES = 3


def _delay():
    """随机延迟，模拟人类操作节奏。"""
    time.sleep(random.uniform(DELAY_MIN_SEC, DELAY_MAX_SEC))


# ============================================================
# 子命令：login - 保存灰豚登录态
# ============================================================
def cmd_login():
    """启动 Playwright，让用户手动登灰豚，保存 storage_state。"""
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("→ 即将启动 Playwright 浏览器（Chromium）")
    print("→ 请在浏览器里手动登灰豚（账号密码 / 微信扫码均可）")
    print("→ 登成功后回到这里按 Enter，脚本会保存登录态到 session 文件")
    print(f"→ session 文件路径：{SESSION_FILE}")
    print("  （已加 .gitignore 屏蔽，不会进 git）")
    print()

    sync_playwright = _require_playwright()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(HUITUN_BASE)

        input("\n>>> 登录完成后按 Enter 继续，按 Ctrl+C 取消 ...")

        context.storage_state(path=str(SESSION_FILE))
        print(f"\n✓ 登录态已保存到 {SESSION_FILE}")
        print("✓ 之后用 `python huitun_collect.py search ...` 即可（不用再登）")

        browser.close()


# ============================================================
# 子命令：explore - 交互式探索灰豚 UI（开发用）
# ============================================================
def cmd_explore():
    """加载 session 进灰豚，提供交互式 REPL 探索 DOM 结构。"""
    if not SESSION_FILE.exists():
        sys.stderr.write(
            f"Error: session 文件不存在: {SESSION_FILE}\n"
            f"先跑：python huitun_collect.py login\n"
        )
        sys.exit(1)

    print("→ 加载已保存的 session...")
    print("→ 浏览器打开后进入交互式 REPL，可输入以下命令探索：")
    print()
    print("    url <url>              跳转到 URL")
    print("    title                  打印页面标题 + URL")
    print("    html <selector>        打印元素 outerHTML（截前 2000 字）")
    print("    text <selector>        打印元素文本")
    print("    count <selector>       打印匹配元素数量")
    print("    eval <js>              执行 JS 并打印结果")
    print("    screenshot <path>      截图到指定路径")
    print("    save                   保存当前 cookie（如登录态更新）")
    print("    exit                   退出（不保存）")
    print()

    sync_playwright = _require_playwright()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(SESSION_FILE))
        page = context.new_page()
        page.goto(HUITUN_BASE)

        while True:
            try:
                cmd = input("\nexplore> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not cmd:
                continue
            if cmd == "exit":
                break
            if cmd == "save":
                context.storage_state(path=str(SESSION_FILE))
                print(f"✓ 已更新 {SESSION_FILE}")
                continue
            if cmd == "title":
                print(f"标题: {page.title()}")
                print(f"URL:  {page.url}")
                continue
            if cmd.startswith("url "):
                url = cmd[4:].strip()
                page.goto(url)
                continue
            if cmd.startswith("html "):
                sel = cmd[5:].strip()
                try:
                    html = page.locator(sel).first.evaluate("e => e.outerHTML")
                    print(html[:2000])
                except Exception as e:
                    print(f"Error: {e}")
                continue
            if cmd.startswith("text "):
                sel = cmd[5:].strip()
                try:
                    txt = page.locator(sel).first.text_content()
                    print((txt or "")[:1000])
                except Exception as e:
                    print(f"Error: {e}")
                continue
            if cmd.startswith("count "):
                sel = cmd[6:].strip()
                try:
                    print(f"匹配数: {page.locator(sel).count()}")
                except Exception as e:
                    print(f"Error: {e}")
                continue
            if cmd.startswith("eval "):
                js = cmd[5:].strip()
                try:
                    result = page.evaluate(js)
                    print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
                except Exception as e:
                    print(f"Error: {e}")
                continue
            if cmd.startswith("screenshot "):
                path = cmd[11:].strip()
                page.screenshot(path=path, full_page=True)
                print(f"✓ 截图保存到 {path}")
                continue
            print(f"未知命令: {cmd}")

        browser.close()


# ============================================================
# 子命令：search - 主采集逻辑
# ============================================================
def _search_one_keyword(page, keyword: str, date_range: str, max_per_keyword: int) -> list:
    """
    对单个关键词执行搜索 + 抓取，返回笔记 dict 列表。

    ⚠️ TODO: 以下 selector 是 placeholder，必须经 explore 阶段后填实。
    """
    notes = []

    sys.stderr.write(f"  → 搜索关键词: '{keyword}'\n")
    _delay()

    # TODO (PLACEHOLDER - 待 explore 阶段确认):
    # 1) 跳转到灰豚小红书爆款搜索页
    #    page.goto(f"{HUITUN_BASE}/xhs/note-search?keyword={keyword}")
    #
    # 2) 等加载 + 切到笔记 tab
    #    page.wait_for_selector('.tab-note', timeout=10000)
    #    page.click('.tab-note')
    #
    # 3) 按互动数降序排序
    #    page.click('button:has-text("互动")')
    #
    # 4) 选时间范围（"近 7 天"等）
    #    page.click(f'button:has-text("近 {date_range}")')
    #
    # 5) 抓列表行（每行一条笔记）
    #    rows = page.locator('.note-row').all()
    #    for row in rows[:max_per_keyword]:
    #        notes.append({
    #            "url": row.locator('a').get_attribute('href'),
    #            "title": row.locator('.title').text_content().strip(),
    #            "author": row.locator('.author').text_content().strip(),
    #            "note_type": "video" if row.locator('.icon-video').count() else "graphic",
    #            "publish_date": row.locator('.date').text_content().strip(),
    #            "likes": _parse_count(row.locator('.likes').text_content()),
    #            "collects": _parse_count(row.locator('.collects').text_content()),
    #            "comments": _parse_count(row.locator('.comments').text_content()),
    #        })
    #        _delay()
    #
    # 6) 翻页（如有需要 + 还没到 max_per_keyword）

    sys.stderr.write(
        f"  ⚠️  selector 待 explore 阶段确认。当前返回空列表。\n"
        f"  ⚠️  开发流程：先跑 `python huitun_collect.py explore` 探索灰豚 UI 后填实。\n"
    )

    return notes


def _parse_count(text: str) -> int:
    """灰豚的数字可能是 '3.5w' / '1.2万' / '123' 等格式，统一转 int。"""
    if not text:
        return 0
    text = text.strip().replace(",", "")
    try:
        if text.endswith("w") or text.endswith("万"):
            return int(float(text.rstrip("w万")) * 10000)
        if text.endswith("k") or text.endswith("千"):
            return int(float(text.rstrip("k千")) * 1000)
        return int(float(text))
    except (ValueError, AttributeError):
        return 0


def cmd_search(args):
    """主采集流程：登录态加载 → 按关键词搜索 → 抓列表 → 输出 JSON。"""
    if not SESSION_FILE.exists():
        sys.stderr.write(
            f"Error: session 文件不存在: {SESSION_FILE}\n"
            f"先跑：python huitun_collect.py login\n"
        )
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    keywords = [k.strip() for k in args.niche.split(",")] if args.niche else DEFAULT_NICHE_KEYWORDS

    # 每个关键词分配的额度（总 top_n / 关键词数量，至少 5）
    per_keyword = max(5, args.top // len(keywords) + 1)

    sys.stderr.write(
        f"→ 关键词清单 ({len(keywords)} 个): {keywords}\n"
        f"→ 每个关键词最多抓 {per_keyword} 条，总目标 {args.top} 条\n"
        f"→ Headless 模式: {args.headless}\n"
    )

    all_notes = []

    sync_playwright = _require_playwright()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(storage_state=str(SESSION_FILE))
        page = context.new_page()

        try:
            for keyword in keywords:
                if len(all_notes) >= MAX_NOTES_PER_SESSION:
                    sys.stderr.write(f"⚠️  已达单次会话上限 {MAX_NOTES_PER_SESSION} 条，提前结束\n")
                    break

                for attempt in range(MAX_RETRIES):
                    try:
                        notes = _search_one_keyword(page, keyword, args.date_range, per_keyword)
                        all_notes.extend(notes)
                        break  # 成功
                    except Exception as e:
                        sys.stderr.write(
                            f"  ⚠️  抓取失败 ({attempt + 1}/{MAX_RETRIES}): {e}\n"
                            f"  ⚠️  等 {RETRY_BACKOFF_SEC} 秒后重试...\n"
                        )
                        time.sleep(RETRY_BACKOFF_SEC)
                else:
                    sys.stderr.write(f"  ❌ '{keyword}' 三次失败，跳过\n")

                _delay()

                if len(all_notes) >= args.top:
                    sys.stderr.write(f"✓ 已达 top {args.top}，提前结束\n")
                    break

        finally:
            browser.close()

    # 去重（按 URL）
    seen_urls = set()
    deduped = []
    for note in all_notes:
        url = note.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(note)

    # 截到 top_n
    final_notes = deduped[: args.top]

    # 组装输出
    output = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": "huitun",
        "query": {
            "niche": args.niche or "default-keywords",
            "keywords_used": keywords,
            "date_range": args.date_range,
            "sort_by": "interaction",
            "top_n": args.top,
        },
        "stats": {
            "total_raw": len(all_notes),
            "after_dedup": len(deduped),
            "final": len(final_notes),
        },
        "notes": final_notes,
    }

    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    sys.stderr.write(
        f"\n✓ 已保存 {len(final_notes)} 条笔记到 {output_path}\n"
        f"  原始抓取 {len(all_notes)} → 去重后 {len(deduped)} → 截取 top {args.top}\n"
    )


# ============================================================
# CLI 入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="灰豚数据小红书爆款采集（Phase 4.4 step 1: 采集）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="详见文件头注释",
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    sub.add_parser("login", help="首次登灰豚 + 保存 session.json（一次即可）")

    sub.add_parser("explore", help="交互式探索灰豚 UI（开发用，定 selector）")

    p_search = sub.add_parser("search", help="采集爆款笔记")
    p_search.add_argument(
        "--niche",
        type=str,
        help="赛道关键词（逗号分隔；不传用默认路飞场景清单）",
    )
    p_search.add_argument(
        "--date-range",
        type=str,
        default="7d",
        choices=["1d", "3d", "7d", "30d"],
        help="时间范围（默认 7d）",
    )
    p_search.add_argument(
        "--top",
        type=int,
        default=30,
        help="采集 top N 条（默认 30）",
    )
    p_search.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="输出 JSON 路径",
    )
    p_search.add_argument(
        "--headless",
        action="store_true",
        help="无头模式（默认 False，首次跑显示浏览器证明是真人操作模式，更不易触发反爬）",
    )

    args = parser.parse_args()

    if args.cmd == "login":
        cmd_login()
    elif args.cmd == "explore":
        cmd_explore()
    elif args.cmd == "search":
        cmd_search(args)


if __name__ == "__main__":
    main()
