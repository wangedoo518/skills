# 路飞知识水电站落地实施计划

更新时间：2026-05-24

## 目标

把现有 `xhs-content-pipeline` 从“小红书内容生产链路”升级为“路飞知识水电站”的 skills 层：

```text
路飞个人微信 DM
  → Elon Mask / lufei-ceo
  → Hermes Kanban Engine
  → Larry / Reed / Jobs / Altman / Satya / Bezos
  → lufei-xhs-wiki / Obsidian
```

未来客户侧入口：

```text
客户微信客服入口
  → Bezos / lufei-bezos
  → 线索收集 / 初步答疑 / CRM 入库
  → Hermes Kanban / lufei-xhs-wiki
```

## 已有能力

| 能力 | 当前实现 |
|---|---|
| 爆款拆解 | `xhs-viral-analysis` 十维拆解 |
| 选题 | `xhs-topic-selection` 50 候选 → Top5 |
| 逐字稿 | `xhs-script-generation` 互动标注版逐字稿 |
| 评论情报 | `xhs-comment-intelligence` |
| 单 skill 调试 | `run_skill.py` |
| 小红书/腾讯会议/Obsidian 工具 | 在 `hermes-agent` 仓库侧实现，skills 仓库负责提示词和角色协议 |

## 本轮新增能力

| Skill | 角色 | 作用 |
|---|---|---|
| `lufei-ops-orchestrator` | Elon Mask | 内部运营入口，拆 Kanban 任务 |
| `lufei-data-intake` | Larry Page | 小红书/腾讯会议/有道/课程/咨询 raw 入库协议 |
| `lufei-content-studio` | Reed Hastings | 集成爆款拆解 → 50 选题 → Top5 → 逐字稿 |
| `lufei-service-diagnosis` | Steve Jobs | 简历/作品集/面试复盘/课程咨询的服务诊断 |
| `lufei-member-cs` | Bezos | 客户微信客服入口，线索收集、初步答疑、CRM 入库 |
| `lufei-quality-gate` | Sam Altman | 反幻觉、引用、人设、交付边界质量门 |
| `lufei-system-integration` | Satya Nadella | Hermes/微信/看板/Obsidian 联调与故障定位 |

## 分步执行计划

### Step 1：文档对齐

- 更新 README 当前状态。
- 更新 CLAUDE 项目身份，把范围从单纯内容 pipeline 扩展到路飞知识水电站 v0.1。
- 写清内部入口与未来客户入口的边界。

验收：

- `README.md` 能看到 9 个 skill。
- `CLAUDE.md` 不再写“私域/CRM 完全不在范围内”。

### Step 2：角色 skill 落盘

- 新增五个路飞专属 skill。
- 每个 skill 有角色、输入契约、输出契约、行为约束。

验收：

- `python xhs-content-pipeline/tests/static_skill_check.py` 通过。

### Step 3：run_skill.py 接入

- `run_skill.py` 增加新 skill 短名映射。
- 继续保持单 skill 原子调用，不在脚本里硬编码 pipeline。

验收：

- `python xhs-content-pipeline/run_skill.py --help` 展示新 skill。
- `load_skill()` 能加载所有新增 skill。

### Step 4：内部运营 happy path

测试输入：

```text
帮我分析这条小红书链接，输出爆款拆解、下一条 Top5 选题和一版互动标注逐字稿，并保存到 lufei-xhs-wiki。
```

预期分派：

1. Elon Mask 创建 Kanban。
2. Larry 提取小红书。
3. Reed 串 `viral-analysis → topic-selection → script-generation`。
4. Sam Altman 做质量门。
5. Satya 检查 Obsidian 写入。

### Step 5：客户客服/CRM happy path

测试输入：

```text
老师，我今天面试完了，感觉答得很乱，想让你帮我复盘一下。
```

预期分派：

1. Bezos 判断 `interview_retro`。
2. 生成微信首轮回复。
3. 生成 CRM 字段。
4. 交 Steve Jobs 做复盘流程。
5. Sam Altman 检查是否过度承诺。

## 暂不做

- 自动发布小红书。
- 机器人刷评/批量控评。
- 直接构建收费 SKU。
- 自动承诺模拟面试机器人定价。
- 用 run_skill.py 写死多步 pipeline。

## 下一步

完成本轮 skills 层后，再到 `hermes-agent` 仓库做 Profile/Kanban worker 绑定和实际微信入口联调。
