# 项目：路飞知识水电站 Skills

> 给打开本目录的 Agent：这是当前项目大脑。以本文为准，不要再沿用 2026-05-19 的“只做小红书爆款链路”旧范围。

## 1. 当前定位

| 项 | 内容 |
|---|---|
| 仓库 | `/Users/champion/Documents/develop/skills` |
| 主体 | `xhs-content-pipeline/` |
| 运行时 | `/Users/champion/Documents/develop/hermes-agent` |
| 样板 IP | 路飞设计沉思录 |
| 目标 | 用 Hermes 把路飞的小红书运营、资料沉淀、服务诊断、客户线索变成一个 AI 运营团队 |

本仓库负责 **skills / prompt / 协议层**。Hermes 网关、微信、Kanban、Obsidian 写入、小红书/腾讯会议工具主要在 `hermes-agent` 仓库。

## 2. 总架构

```text
路飞个人微信 DM
  → Elon Mask / lufei-ceo
  → Hermes Kanban Engine
  → Larry / Reed / Jobs / Altman / Satya / Bezos
  → lufei-xhs-wiki / Obsidian

客户微信客服入口（未来收费 SKU 入口）
  → Bezos / lufei-bezos
  → 线索收集 / 初步答疑 / CRM 入库
  → Hermes Kanban / lufei-xhs-wiki
```

## 3. 已落地 Skill

| Skill | 角色 | 状态 |
|---|---|---|
| `xhs-viral-analysis` | Reed Hastings | ✅ 小红书十维爆款拆解 |
| `xhs-topic-selection` | Reed Hastings | ✅ 50 个候选 → Top5 |
| `xhs-script-generation` | Reed Hastings | ✅ 互动标注逐字稿 |
| `xhs-comment-intelligence` | Reed Hastings / Bezos | ✅ 评论区需求、关键词、转化线索 |
| `lufei-ops-orchestrator` | Elon Mask | ✅ 内部微信/Chat 输入 → Kanban 卡片 |
| `lufei-data-intake` | Larry Page | ✅ 小红书/腾讯会议/有道/课程/咨询 raw 入库协议 |
| `lufei-content-studio` | Reed Hastings | ✅ 集成爆款拆解 → 选题 → 逐字稿 |
| `lufei-service-diagnosis` | Steve Jobs | ✅ 简历/作品集/面试复盘/课程咨询流程 |
| `lufei-member-cs` | Bezos | ✅ 客户微信客服入口、CRM 字段、首轮回复 |
| `lufei-quality-gate` | Sam Altman | ✅ 引用/幻觉/人设/交付边界检查 |
| `lufei-system-integration` | Satya Nadella | ✅ Hermes/微信/Kanban/Obsidian 联调检查 |

## 4. 当前可测试链路

### 内部运营链路

```text
路飞输入：帮我拆这条小红书，给 Top5 选题和一版逐字稿
  → lufei-ops-orchestrator
  → lufei-data-intake
  → lufei-content-studio
  → lufei-quality-gate
  → lufei-system-integration
```

### 客户线索链路

```text
客户输入：老师，我今天面试完了，感觉答得很乱，想复盘
  → lufei-member-cs
  → lufei-service-diagnosis
  → lufei-quality-gate
  → CRM / Obsidian
```

## 5. 快速自测

```bash
cd /Users/champion/Documents/develop/skills
python xhs-content-pipeline/tests/static_skill_check.py
python xhs-content-pipeline/run_skill.py --help
python -m py_compile xhs-content-pipeline/run_skill.py xhs-content-pipeline/tests/static_skill_check.py
```

预期：

```text
OK 11 skills registered and loadable
```

## 6. 开发纪律

1. `run_skill.py` 只做单 skill 原子调用，不硬编码多步 pipeline。
2. 多步编排交给 Hermes Kanban/Profile。
3. 小红书真实数据必须来自 `xhs_extract_note` / `xhs_extract_profile_notes` / 真实转写 / 真实评论，不允许脑补。
4. 客户问题必须先入 CRM 字段，再考虑答复或转人工。
5. 所有服务建议不得承诺 offer、过筛、录取结果。
6. 所有可交付产物最终必须过 `lufei-quality-gate`。
7. Obsidian/llm-wiki 中的结论页必须能追溯 raw 来源。

## 7. 下一步

1. 在 `hermes-agent` 仓库把这些 skill 绑定到对应 Profiles。
2. 让 Hermes Kanban 使用 `lufei-ops-orchestrator` 生成卡片。
3. 用一条小红书链接跑通：提取 → 拆解 → Top5 → 逐字稿 → 质量门 → Obsidian。
4. 用一条客户咨询消息跑通：客服分类 → CRM → 服务诊断 → 质量门。
