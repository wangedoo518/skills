#!/usr/bin/env python3
"""
run_skill.py —— 用 FreeModel API 调用任意 SKILL

按 ADR-015 Agent-first 原则：本脚本是单一原子能力（"调一次 SKILL"），
不是 pipeline。pipeline 编排由 agent / 用户在更高层完成。

用法：
    # 拆解一条逐字稿
    python run_skill.py viral-analysis -i ./tests/路飞_vol13.txt -o ./reports/vol13.md

    # 选题推荐（输入是 JSON 格式的博主画像 + 拆解报告路径）
    python run_skill.py topic-selection -i ./inputs/路飞_input.json -o ./outputs/选题.md

    # 生成逐字稿
    python run_skill.py script-generation -i ./inputs/vol14_input.json -o ./outputs/vol14.md

    # 深挖评论区
    python run_skill.py comment-intelligence -i ./inputs/comments.md -o ./outputs/comment_report.md

    # 路飞知识水电站：内部运营编排
    python run_skill.py lufei-ops -i ./inputs/weixin_dm.md -o ./outputs/kanban_cards.md

    # 从 stdin 读取
    cat transcript.txt | python run_skill.py viral-analysis

环境变量（或写到 .env）：
    FREEMODEL_API_KEY     必填
    FREEMODEL_BASE_URL    默认 https://api.freemodel.dev/v1
    FREEMODEL_MODEL       默认 gpt-5.5
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    sys.stderr.write("Error: 缺少 openai 库，运行: pip install -r requirements.txt\n")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv 可选

SKILLS_DIR = Path(__file__).parent / "skills"

# 短名 → 全名映射
SKILL_MAP = {
    "viral-analysis": "xhs-viral-analysis",
    "script-generation": "xhs-script-generation",
    "topic-selection": "xhs-topic-selection",
    "comment-intelligence": "xhs-comment-intelligence",
    "lufei-ops": "lufei-ops-orchestrator",
    "lufei-orchestrator": "lufei-ops-orchestrator",
    "lufei-larry": "lufei-data-intake",
    "lufei-data": "lufei-data-intake",
    "lufei-reed": "lufei-content-studio",
    "lufei-content": "lufei-content-studio",
    "lufei-service": "lufei-service-diagnosis",
    "lufei-diagnosis": "lufei-service-diagnosis",
    "lufei-cs": "lufei-member-cs",
    "lufei-member-cs": "lufei-member-cs",
    "lufei-qa": "lufei-quality-gate",
    "lufei-quality": "lufei-quality-gate",
    "lufei-integration": "lufei-system-integration",
    # 完整名也支持直接传
    "xhs-viral-analysis": "xhs-viral-analysis",
    "xhs-script-generation": "xhs-script-generation",
    "xhs-topic-selection": "xhs-topic-selection",
    "xhs-comment-intelligence": "xhs-comment-intelligence",
    "lufei-ops-orchestrator": "lufei-ops-orchestrator",
    "lufei-data-intake": "lufei-data-intake",
    "lufei-content-studio": "lufei-content-studio",
    "lufei-service-diagnosis": "lufei-service-diagnosis",
    "lufei-quality-gate": "lufei-quality-gate",
    "lufei-system-integration": "lufei-system-integration",
}


def load_skill(skill_name: str) -> str:
    """加载 SKILL.md 全文作为 system prompt。"""
    full_name = SKILL_MAP.get(skill_name)
    if not full_name:
        raise ValueError(
            f"未知 SKILL: {skill_name}。可用: {list(SKILL_MAP.keys())}"
        )
    skill_path = SKILLS_DIR / full_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"SKILL 文件不存在: {skill_path}")
    return skill_path.read_text(encoding="utf-8")


def run_skill(
    skill_md: str,
    user_input: str,
    model: str = None,
    base_url: str = None,
    api_key: str = None,
    temperature: float = 0.7,
) -> dict:
    """
    调一次 LLM。返回 dict 含 content + usage + model。

    Agent-first 注意：本函数是原子能力，不做任何多步编排。
    多次调用、组合 SKILL、迭代等都由 caller / agent 自己决定。
    """
    api_key = api_key or os.environ.get("FREEMODEL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "缺少 FREEMODEL_API_KEY。设环境变量或建 .env 文件（参考 .env.example）"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url or os.environ.get(
            "FREEMODEL_BASE_URL", "https://api.freemodel.dev/v1"
        ),
    )

    model_id = model or os.environ.get("FREEMODEL_MODEL", "gpt-5.5")

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": skill_md},
            {"role": "user", "content": user_input},
        ],
        temperature=temperature,
    )

    return {
        "content": response.choices[0].message.content,
        "model": response.model,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="用 FreeModel API 调用任意 SKILL（单次原子调用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="详见文件头注释",
    )
    parser.add_argument(
        "skill",
        choices=list(SKILL_MAP.keys()),
        help="SKILL 短名或全名",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="输入文件路径（不指定则从 stdin 读）",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出文件路径（不指定则打印到 stdout）",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="覆盖环境变量里的模型名",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        help="覆盖环境变量里的 API base URL",
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="LLM 温度（默认 0.7）",
    )
    parser.add_argument(
        "--show-usage",
        action="store_true",
        help="在 stderr 打印 token usage",
    )
    args = parser.parse_args()

    # 读 input
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            sys.stderr.write(f"Error: 输入文件不存在: {input_path}\n")
            sys.exit(1)
        user_input = input_path.read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            sys.stderr.write(
                "Error: 没有 --input 也没有 stdin 输入。"
                "用 -i <file> 或 cat file | python run_skill.py ...\n"
            )
            sys.exit(1)
        user_input = sys.stdin.read()

    # 加载 SKILL
    try:
        skill_md = load_skill(args.skill)
    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    # 调 LLM
    sys.stderr.write(f"→ 调用 SKILL: {args.skill}，输入 {len(user_input)} 字符...\n")
    try:
        result = run_skill(
            skill_md=skill_md,
            user_input=user_input,
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature,
        )
    except Exception as e:
        sys.stderr.write(f"Error: LLM 调用失败: {e}\n")
        sys.exit(1)

    # 输出
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result["content"], encoding="utf-8")
        sys.stderr.write(f"✓ 保存到 {output_path}\n")
    else:
        print(result["content"])

    if args.show_usage:
        sys.stderr.write(
            f"→ 模型: {result['model']} | "
            f"prompt: {result['usage']['prompt_tokens']} tok | "
            f"completion: {result['usage']['completion_tokens']} tok | "
            f"total: {result['usage']['total_tokens']} tok\n"
        )


if __name__ == "__main__":
    main()
