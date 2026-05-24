#!/usr/bin/env python3
"""Static checks for the xhs-content-pipeline skill registry."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_skill import SKILL_MAP, load_skill  # noqa: E402


REQUIRED_SKILLS = {
    "xhs-viral-analysis",
    "xhs-script-generation",
    "xhs-topic-selection",
    "xhs-comment-intelligence",
    "lufei-ops-orchestrator",
    "lufei-data-intake",
    "lufei-content-studio",
    "lufei-service-diagnosis",
    "lufei-member-cs",
    "lufei-quality-gate",
    "lufei-system-integration",
}


def main() -> int:
    missing = []
    broken = []

    for skill_name in sorted(REQUIRED_SKILLS):
        skill_path = ROOT / "skills" / skill_name / "SKILL.md"
        if not skill_path.exists():
            missing.append(str(skill_path))
            continue
        content = skill_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            broken.append(f"{skill_name}: missing frontmatter")
        if f"name: {skill_name}" not in content:
            broken.append(f"{skill_name}: frontmatter name mismatch")
        if "## 输出契约" not in content and "## 输出契约" not in content:
            broken.append(f"{skill_name}: missing output contract")

    mapped = set(SKILL_MAP.values())
    unmapped = REQUIRED_SKILLS - mapped
    if unmapped:
        broken.append(f"SKILL_MAP missing: {sorted(unmapped)}")

    for skill_name in sorted(REQUIRED_SKILLS):
        try:
            loaded = load_skill(skill_name)
        except Exception as exc:  # noqa: BLE001
            broken.append(f"{skill_name}: load_skill failed: {exc}")
            continue
        if len(loaded) < 500:
            broken.append(f"{skill_name}: content too short")

    if missing or broken:
        for item in missing:
            print(f"MISSING {item}")
        for item in broken:
            print(f"BROKEN {item}")
        return 1

    print(f"OK {len(REQUIRED_SKILLS)} skills registered and loadable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
