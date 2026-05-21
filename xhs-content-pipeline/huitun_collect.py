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
import io
import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Windows cmd UTF-8 兼容
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass


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
HUITUN_BASE = "https://xhs.huitun.com"  # 红薯版（小红书板块）
WORKBENCH_URL = "https://xhs.huitun.com/#/home"

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
def _parse_count(text):
    """灰豚的数字可能是 '3.5w' / '1.2万' / '123' / '6,102' / '无' 等，统一转 int。"""
    if not text:
        return 0
    text = str(text).strip().replace(",", "").replace("，", "")
    if text in ("无", "-", "—", ""):
        return 0
    try:
        if text.endswith("w") or text.endswith("万"):
            return int(float(text.rstrip("w万")) * 10000)
        if text.endswith("k") or text.endswith("千"):
            return int(float(text.rstrip("k千")) * 1000)
        return int(float(text))
    except (ValueError, AttributeError):
        return 0


NOTE_SEARCH_URL = "https://xhs.huitun.com/#/note/note_search"


def _enter_note_search_page(page):
    """Goto 笔记查找页 + 关 modal。"""
    # 关闭可能的二维码 modal
    try:
        page.evaluate("""() => {
            document.querySelectorAll('.ant-modal-wrap, .ant-modal-mask').forEach(m => m.remove());
        }""")
    except Exception:
        pass

    page.goto(NOTE_SEARCH_URL, wait_until="domcontentloaded", timeout=20000)
    time.sleep(5)  # 等 SPA + 列表加载

    # 验证列表有数据
    row_count = page.locator("tr.ant-table-row").count()
    if row_count == 0:
        raise RuntimeError(f"笔记查找页没有列表行，URL={page.url}（session 可能失效）")
    sys.stderr.write(f"  → 进入笔记查找页 ({row_count} 行)\n")


def _maybe_search_keyword(page, keyword):
    """在笔记查找页输入关键词搜索（精准匹配专用框，避开顶部全局搜索）。"""
    if not keyword:
        return False
    try:
        cnt = page.locator("input[placeholder='搜索笔记标题/关键词']").count()
        if cnt == 0:
            sys.stderr.write(f"  ⚠ 没找到笔记搜索框（页面结构变了？）\n")
            return False
        search_input = page.locator("input[placeholder='搜索笔记标题/关键词']").first
        search_input.fill(keyword, timeout=5000)
        time.sleep(0.5)
        search_input.press("Enter")
        time.sleep(6)
        return True
    except Exception as e:
        sys.stderr.write(f"  ⚠ 搜索 '{keyword}' 失败: {e}\n")
        return False


def _extract_notes_from_page(page):
    """从当前页面 DOM 抓所有笔记数据，返回 dict 列表。

    数据契约（来自 explore_dump_rows.py 验证）：
      - 每个笔记占 2 行 `tr.ant-table-row`（10 td 主行 + 3 td 扩展行）
      - 同一 data-row-key 的两行合并为一条记录
      - data-row-key 格式: '{type}-{publish_time}-{note_id}'，末段为小红书 note_id
      - 主行 10 td: 笔记信息 / 发布时间 / 预估阅读量 / 互动量 / 点赞 / 收藏 / 评论 / 分享 / 提及品牌 / 操作
      - 扩展行 3 td: 博主基本信息 / 报价 / 粉丝占比
    """
    raw = page.evaluate("""() => {
        const out = {};
        document.querySelectorAll('tr.ant-table-row').forEach(tr => {
            const key = tr.getAttribute('data-row-key');
            if (!key) return;
            const tds = Array.from(tr.querySelectorAll('td')).map(td => (td.innerText || '').trim());
            if (!out[key]) out[key] = { key: key, main: null, extra: null };
            if (tds.length >= 8) {
                // 主行：提取详细 DOM 字段
                const titleEl = tr.querySelector('.styles_note_title__1FLfF');
                const imgEl = tr.querySelector('.styles_note_info__1xd2R img, .styles_note_info__1kDy0 img');
                const durationEl = tr.querySelector('.styles_duration__1weRs span');
                const tagEls = tr.querySelectorAll('.styles_item_tag__1AvT_');
                out[key].main = {
                    tds: tds,
                    title: titleEl ? titleEl.innerText.trim() : null,
                    thumbnail: imgEl ? imgEl.src : null,
                    duration: durationEl ? durationEl.innerText.trim() : null,
                    tags: Array.from(tagEls).map(e => e.innerText.trim()).filter(t => t && t !== '更多...'),
                };
            } else {
                // 扩展行：博主信息
                const authorNameEl = tr.querySelector('.style_one_line__3wm7P');
                const authorAvatarEl = tr.querySelector('img');
                // "粉丝数：293.3wID：460729078"
                const anchorIdxEls = tr.querySelectorAll('.style_anchor_idx__2scpz');
                let followers = null;
                let author_id = null;
                anchorIdxEls.forEach(el => {
                    const t = el.innerText || '';
                    const fm = t.match(/粉丝数[：:]\\s*([\\d.,wkw万千]+)/);
                    if (fm) followers = fm[1];
                    const im = t.match(/ID[：:]\\s*(\\d+)/);
                    if (im) author_id = im[1];
                });
                // 找博主等级（头部达人/腰部达人/素人 等）
                const levelEl = tr.querySelector('.styles_other_type_v2__3BkEW');
                out[key].extra = {
                    tds: tds,
                    author_name: authorNameEl ? authorNameEl.innerText.trim() : null,
                    author_avatar: authorAvatarEl ? authorAvatarEl.src : null,
                    author_id: author_id,
                    author_followers_raw: followers,
                    author_level: levelEl ? levelEl.innerText.trim() : null,
                };
            }
        });
        return Object.values(out);
    }""")

    notes = []
    for r in raw:
        m = r.get("main") or {}
        e = r.get("extra") or {}
        key = r["key"]

        # 解析 note_id from data-row-key (末段)
        parts = key.split("-")
        # 笔记 ID 通常是末段，但因为 publish_time 也含 '-'，要从末尾找最长的 hex 段
        note_id = parts[-1] if parts else key

        # 主行 10 td 顺序: 0=笔记信息 1=发布时间 2=预估阅读 3=互动量 4=点赞 5=收藏 6=评论 7=分享 8=提及品牌 9=操作
        tds = m.get("tds") or []
        if len(tds) < 8:
            continue  # 不完整跳过

        title = m.get("title")
        # 备用：从笔记信息单元拆出标题（第一行）
        if not title and tds[0]:
            title = tds[0].split("\n")[0].strip()
            if title and title[0].isdigit() and ":" in title[:6]:
                # 视频时长(如 "02:19")在前，标题在第 2 行
                lines = tds[0].split("\n")
                title = lines[1] if len(lines) > 1 else title

        likes = _parse_count(tds[4] if len(tds) > 4 else "")
        collects = _parse_count(tds[5] if len(tds) > 5 else "")
        comments = _parse_count(tds[6] if len(tds) > 6 else "")
        shares = _parse_count(tds[7] if len(tds) > 7 else "")

        notes.append({
            "url": f"https://www.xiaohongshu.com/explore/{note_id}",
            "note_id": note_id,
            "row_key": key,
            "title": title,
            "thumbnail": m.get("thumbnail"),
            "note_type": "video" if m.get("duration") else "graphic",
            "duration_seconds": _parse_duration(m.get("duration")),
            "publish_date": (tds[1] if len(tds) > 1 else "").strip(),
            "tags": m.get("tags") or [],
            "predicted_read": _parse_count(tds[2] if len(tds) > 2 else ""),
            "total_interaction": _parse_count(tds[3] if len(tds) > 3 else ""),
            "likes": likes,
            "collects": collects,
            "comments": comments,
            "shares": shares,
            "mentioned_brand": (tds[8] if len(tds) > 8 else "").strip(),
            # CES 算法权重: 点赞×1 + 收藏×1 + 评论×4 + 转发×4 + 关注×8
            # 灰豚无关注数，此处只算前 4 项
            "ces_partial": likes * 1 + collects * 1 + comments * 4 + shares * 4,
            "author": {
                "name": e.get("author_name"),
                "id": e.get("author_id"),
                "avatar": e.get("author_avatar"),
                "level": e.get("author_level"),
                "followers_raw": e.get("author_followers_raw"),
                "followers": _parse_count(e.get("author_followers_raw") or ""),
            },
        })

    return notes


def _parse_duration(s):
    """'02:19' / '14:37' → 秒数；None / 非视频 → None"""
    if not s:
        return None
    m = re.match(r"^(\d+):(\d+)$", s.strip())
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    return None


XHS_NOTE_ID_RE = re.compile(r"/(?:item|explore|discovery/item)/([a-f0-9]{16,32})", re.IGNORECASE)


def _extract_xhs_note_id(url):
    """从小红书 URL 抽取 hex note_id。

    覆盖以下场景：
      - 直接 URL: https://www.xiaohongshu.com/explore/{hex}
      - 直接 URL: https://www.xiaohongshu.com/discovery/item/{hex}?xsec_token=...
      - 未登录 redirect: https://www.xiaohongshu.com/login?redirectPath=https%3A%2F%2F...%2Fitem%2F{hex}
      - 404 redirect: https://www.xiaohongshu.com/404?source=...redirectPath=https%3A%2F%2F...%2Fexplore%2F{hex}
    """
    if not url:
        return None
    from urllib.parse import unquote
    # 反复 unquote 几次（可能多层编码）
    decoded = url
    for _ in range(3):
        new = unquote(decoded)
        if new == decoded:
            break
        decoded = new
    m = XHS_NOTE_ID_RE.search(decoded)
    return m.group(1) if m else None


def _resolve_real_xhs_url_by_index(context, page, idx, max_retries=2):
    """
    点击第 idx 个"原文"按钮 → 拿新 tab 真小红书 URL → 关 tab。
    返回 (real_url, hex_note_id) 或 (None, None)。
    """
    for attempt in range(max_retries):
        try:
            yuan_wen = page.locator("text=原文").nth(idx)
            try:
                yuan_wen.scroll_into_view_if_needed(timeout=3000)
                time.sleep(0.3)
            except Exception:
                pass

            with context.expect_page(timeout=10000) as new_page_info:
                yuan_wen.click(force=True, timeout=3000)
            new_page = new_page_info.value
            time.sleep(0.8)  # 等 URL 稳定 (redirect)
            real_url = new_page.url
            try:
                new_page.close()
            except Exception:
                pass
            hex_id = _extract_xhs_note_id(real_url)
            if hex_id:
                return real_url, hex_id
            else:
                sys.stderr.write(f"      ⚠ idx={idx} 新 tab URL 不含 hex: {real_url[:120]}\n")
                return real_url, None  # URL 有但抽不出 hex
        except Exception as e:
            sys.stderr.write(f"      ⚠ idx={idx} attempt {attempt+1} failed: {str(e)[:80]}\n")
            if attempt < max_retries - 1:
                time.sleep(1.5)  # 重试前等
    return None, None


def _search_one_keyword(page, keyword: str, date_range: str, max_per_keyword: int) -> list:
    """对单个关键词（或不带关键词）执行搜索 + 抓取，返回笔记列表。"""
    sys.stderr.write(f"  → 关键词: '{keyword or '(默认热门)'}'\n")
    _delay()

    # 1) 进笔记查找页（如果还没进）
    if "/note_search" not in page.url:
        try:
            _enter_note_search_page(page)
        except Exception as e:
            sys.stderr.write(f"  ⚠ 进笔记查找页失败: {e}\n")
            return []

    # 2) 输关键词搜索（如果有）
    if keyword:
        _maybe_search_keyword(page, keyword)

    # 3) 等列表加载稳定
    try:
        page.wait_for_selector("tr.ant-table-row", timeout=15000)
        time.sleep(2)  # 给图片懒加载等时间
    except Exception as e:
        sys.stderr.write(f"  ⚠ 未找到列表: {e}\n")
        return []

    # 4) 抓数据
    notes = _extract_notes_from_page(page)
    sys.stderr.write(f"  ← 抓到 {len(notes)} 条\n")

    # 5) 截到 max（先截再 resolve，省 click 次数）
    notes = notes[:max_per_keyword]

    # 6) 为每条 click "原文" 拿真小红书 URL + hex note_id
    context = page.context
    sys.stderr.write(f"  → 解析真小红书 URL ({len(notes)} 条, 约 +{len(notes)*3}s) ...\n")
    for i, n in enumerate(notes):
        real_url, hex_id = _resolve_real_xhs_url_by_index(context, page, i)
        if real_url and hex_id:
            n["url"] = f"https://www.xiaohongshu.com/explore/{hex_id}"
            n["xhs_note_id"] = hex_id
            n["raw_xhs_url"] = real_url  # 含 xsec_token 的完整 URL
            n["huitun_note_id"] = n["note_id"]  # 备份灰豚内部 ID
            n["note_id"] = hex_id  # 主 note_id = 小红书 hex
        else:
            n["url"] = None
            n["xhs_note_id"] = None
            n["huitun_note_id"] = n["note_id"]
        time.sleep(random.uniform(0.5, 1.5))  # 反爬

    return notes


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

        # 启动浏览器后先 navigate 到红薯版工作台
        sys.stderr.write(f"→ 导航到 {WORKBENCH_URL}\n")
        try:
            page.goto(WORKBENCH_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            sys.stderr.write(f"⚠ goto 失败: {e}\n")
        time.sleep(5)  # 等 SPA JS 渲染
        sys.stderr.write(f"→ 落地 URL: {page.url}\n")

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

    # 去重（按 row_key，覆盖 resolve 失败 URL=None 情况）
    seen_keys = set()
    deduped = []
    for note in all_notes:
        k = note.get("row_key") or note.get("note_id")
        if k and k not in seen_keys:
            seen_keys.add(k)
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
