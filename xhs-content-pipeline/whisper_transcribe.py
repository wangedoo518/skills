#!/usr/bin/env python3
"""
whisper_transcribe.py —— 用 faster-whisper 本地转写音视频

按 ADR-015 Agent-first 原则：本脚本是单一原子能力（"音视频 → 文字"），
不做任何后续处理（不调 SKILL、不格式化拼接到模板）。组合由 caller / agent 完成。

用法：
    # 转一条视频，输出纯文本逐字稿
    python whisper_transcribe.py video.mp4 -o transcript.txt

    # 输出带时间戳的 SRT 字幕
    python whisper_transcribe.py video.mp4 -f srt -o subs.srt

    # 用大模型 + 强制中文
    python whisper_transcribe.py video.mp4 --model large-v3 --language zh

    # 从 stdout 看
    python whisper_transcribe.py audio.m4a

依赖：
    pip install -r requirements-transcribe.txt

模型尺寸 vs 准确度 vs 速度（首次运行自动下载）：
    tiny     39M   最快  准确度低（够听个大概）
    base     74M   快
    small    244M  中    短中文可用
    medium   769M  稍慢  ← 默认（中文小红书短视频够用）
    large-v2 1.5G  慢
    large-v3 1.5G  最慢  最准（推荐做正式素材分析）
"""
import argparse
import json
import sys
from pathlib import Path


def _require_whisper():
    """延迟 import faster-whisper，让 --help 即使没装也能看。"""
    try:
        from faster_whisper import WhisperModel
        return WhisperModel
    except ImportError:
        sys.stderr.write(
            "Error: 缺少 faster-whisper。运行: pip install -r requirements-transcribe.txt\n"
        )
        sys.exit(1)


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


def transcribe(
    input_path: Path,
    model_name: str = "medium",
    language: str = None,
    device: str = "cpu",
    compute_type: str = "int8",
    beam_size: int = 5,
) -> tuple:
    """
    转写音视频。

    返回 (segments, info)，segments 是 list of dict 含 start/end/text。
    """
    WhisperModel = _require_whisper()

    sys.stderr.write(
        f"→ 加载模型 {model_name} (device={device}, compute={compute_type})\n"
        f"→ 首次使用会下载模型，请稍等...\n"
    )
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    sys.stderr.write(f"→ 开始转写: {input_path.name}\n")
    segments_iter, info = model.transcribe(
        str(input_path),
        language=language,  # None = auto-detect
        vad_filter=True,  # 跳过静音
        beam_size=beam_size,
    )

    sys.stderr.write(
        f"→ 检测语言: {info.language} (置信度 {info.language_probability:.2f})\n"
        f"→ 音频时长: {info.duration:.1f}s\n"
    )

    segments = []
    for i, segment in enumerate(segments_iter):
        segments.append({
            "id": i,
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
        })
        sys.stderr.write(
            f"\r→ 转写中... 段 {i + 1}, 当前 {segment.end:.1f}s / {info.duration:.1f}s"
        )
        sys.stderr.flush()
    sys.stderr.write("\n→ 转写完成\n")

    return segments, info


def format_output(segments: list, fmt: str, info=None) -> str:
    """按格式输出 segments。"""
    if fmt == "plain":
        # 纯文本：合并所有段落，每段一行
        return "\n".join(s["text"] for s in segments)
    elif fmt == "srt":
        lines = []
        for s in segments:
            lines.append(str(s["id"] + 1))
            lines.append(
                f"{format_srt_timestamp(s['start'])} --> {format_srt_timestamp(s['end'])}"
            )
            lines.append(s["text"])
            lines.append("")
        return "\n".join(lines)
    elif fmt == "json":
        return json.dumps(
            {
                "language": info.language if info else None,
                "duration": info.duration if info else None,
                "segments": segments,
            },
            ensure_ascii=False,
            indent=2,
        )
    else:
        raise ValueError(f"未知格式: {fmt}")


def main():
    parser = argparse.ArgumentParser(
        description="用 faster-whisper 本地转写音视频（单次原子调用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="详见文件头注释",
    )
    parser.add_argument("input", type=str, help="音视频文件路径")
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出文件路径（不指定打印到 stdout）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="medium",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="模型尺寸（默认 medium）",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default=None,
        help="强制语言代码（如 zh, en）；不指定则自动检测",
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        default="plain",
        choices=["plain", "srt", "json"],
        help="输出格式（默认 plain）",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="cpu 或 cuda（需要 CUDA 环境，默认 cpu）",
    )
    parser.add_argument(
        "--compute-type",
        type=str,
        default="int8",
        choices=["int8", "int8_float16", "float16", "float32"],
        help="计算精度（默认 int8 省内存）",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="beam search 大小（默认 5，越大越准越慢）",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.stderr.write(f"Error: 输入文件不存在: {input_path}\n")
        sys.exit(1)

    try:
        segments, info = transcribe(
            input_path,
            model_name=args.model,
            language=args.language,
            device=args.device,
            compute_type=args.compute_type,
            beam_size=args.beam_size,
        )
    except Exception as e:
        sys.stderr.write(f"Error: 转写失败: {e}\n")
        sys.exit(1)

    output_text = format_output(segments, args.format, info)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_text, encoding="utf-8")
        sys.stderr.write(f"✓ 保存到 {out_path} ({len(segments)} 段, {info.duration:.1f}s 音频)\n")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
