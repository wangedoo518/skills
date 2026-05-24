# 路飞知识水电站 Skills (xhs-content-pipeline)

针对「路飞设计沉思录」设计师职业发展 + 大厂求职垂类调优的 AI 运营 skills 层。

当前仓库不再只是单条小红书内容生产工具，而是路飞知识水电站的提示词与 skill 协议层：

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

## 当前状态

| 模块 | 状态 |
|------|------|
| **拆解 SKILL** (`xhs-viral-analysis` v0.3.0) | ✅ 已落地，十维框架（钩子/框架/爆点/情绪/阈值/评论资产/互动动机/留存完播/下一条选题/script_brief） |
| **生成 SKILL** (`xhs-script-generation` v0.2.0) | ✅ 已落地，视频/图文双骨架 + 互动设计标注版逐字稿 + 评论区设计 + 12 条反爆款保护 |
| **选题 SKILL** (`xhs-topic-selection` v0.2.0) | ✅ 已落地，50 个候选 → Top 5 + 五维评分（匹配/痛点/收藏/评论/执行） |
| **评论情报 SKILL** (`xhs-comment-intelligence` v0.1) | ✅ 已落地，评论需求/店铺/关键词/争议/转化线索分析 |
| **路飞内部运营编排** (`lufei-ops-orchestrator` v0.1) | ✅ 已落地，微信/Chat 意图 → Kanban 卡片 → worker 分派 |
| **路飞资料提取** (`lufei-data-intake` v0.1) | ✅ 已落地，小红书/腾讯会议/有道/课程/咨询 raw 入库协议 |
| **路飞内容工作室** (`lufei-content-studio` v0.1) | ✅ 已落地，集成爆款拆解 → 选题 → 逐字稿 |
| **路飞服务诊断** (`lufei-service-diagnosis` v0.1) | ✅ 已落地，简历/作品集/面试复盘/课程咨询流程设计 |
| **路飞客户客服/CRM** (`lufei-member-cs` v0.1) | ✅ 已落地，客户意图分类、首轮回复、CRM 字段 |
| **路飞质量门** (`lufei-quality-gate` v0.1) | ✅ 已落地，引用/幻觉/人设/交付边界检查 |
| **路飞系统集成** (`lufei-system-integration` v0.1) | ✅ 已落地，Hermes/微信/Kanban/Obsidian 联调与故障定位 |
| **`run_skill.py` 调用脚本** | ✅ 已落地，接 FreeModel API |
| **`whisper_transcribe.py` 转写脚本** | ✅ 已落地，本地 faster-whisper |
| **`huitun_collect.py` 灰豚采集脚本** | 🟡 骨架已落地（login + explore + search 三命令），search 的 selector 待 explore 阶段填实 |
| **Hermes Plugin 集成** | ✅ 已有 `plugin.yaml` + `__init__.py`，skills 层主要负责 prompt/协议 |
| **复盘 SKILL** | ⏸ 待 Phase 6（需要发布后真实数据） |

## 目录结构

```
xhs-content-pipeline/
├── README.md                              ← 本文件
├── .env.example                           ← 复制为 .env 后填 API key
├── requirements.txt                       ← Python 依赖
├── run_skill.py                           ← ✅ CLI: 用 FreeModel 跑任意 SKILL
├── whisper_transcribe.py                  ← ✅ CLI: faster-whisper 本地音视频转写
├── requirements-transcribe.txt            ← ✅ 转写脚本的可选依赖
├── huitun_collect.py                      ← 🟡 CLI: 灰豚 Playwright 采集（骨架就绪，selector 待 explore）
├── requirements-collect.txt               ← ✅ 采集脚本的可选依赖（playwright）
├── skills/
│   ├── xhs-viral-analysis/SKILL.md       ← 拆解 v0.3.0
│   ├── xhs-script-generation/SKILL.md    ← 生成 v0.2.0
│   ├── xhs-topic-selection/SKILL.md      ← 选题 v0.2.0
│   ├── xhs-comment-intelligence/SKILL.md ← 评论情报 v0.1
│   ├── lufei-ops-orchestrator/SKILL.md   ← Elon Mask / Kanban 编排
│   ├── lufei-data-intake/SKILL.md        ← Larry Page / 资料提取
│   ├── lufei-content-studio/SKILL.md     ← Reed Hastings / 内容工作室
│   ├── lufei-service-diagnosis/SKILL.md  ← Steve Jobs / 服务诊断
│   ├── lufei-member-cs/SKILL.md          ← Bezos / 客服 CRM
│   ├── lufei-quality-gate/SKILL.md       ← Sam Altman / 质量门
│   └── lufei-system-integration/SKILL.md ← Satya Nadella / 系统集成
├── docs/
│   └── 2026-05-24-lufei-knowledge-hydropower-implementation.md
├── tests/
│   └── static_skill_check.py
└── plugin.yaml                            ← Hermes 插件清单
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API key

```bash
cp .env.example .env
# 编辑 .env 填入 FREEMODEL_API_KEY
```

或直接设环境变量：
```bash
export FREEMODEL_API_KEY=sk-your-key-here
```

### 3. 跑 SKILL

#### 拆解一条爆款逐字稿

```bash
# 准备输入文件
cat > /tmp/transcript.txt <<EOF
（粘贴某条小红书视频的逐字稿、标题、互动数据）
EOF

# 拆解
python run_skill.py viral-analysis -i /tmp/transcript.txt -o /tmp/report.md
```

#### 选题推荐

```bash
# 输入: 博主画像 + 拆解报告
python run_skill.py topic-selection -i /tmp/路飞_input.md -o /tmp/选题.md
```

#### 评论区情报分析

```bash
# 输入: note.md / note.json 摘要 / 评论截图 OCR / 评论列表
python run_skill.py comment-intelligence -i /tmp/comments_input.md -o /tmp/comment_report.md
```

#### 生成逐字稿

```bash
python run_skill.py script-generation -i /tmp/vol14_input.md -o /tmp/vol14稿.md
```

#### 路飞内部运营编排

```bash
python run_skill.py lufei-ops -i /tmp/weixin_dm.md -o /tmp/kanban_cards.md
```

#### 客户客服 / CRM 入库

```bash
python run_skill.py lufei-cs -i /tmp/customer_message.md -o /tmp/crm_intake.md
```

#### 简历 / 作品集 / 面试复盘诊断

```bash
python run_skill.py lufei-service -i /tmp/student_case.md -o /tmp/service_diagnosis.md
```

#### 质量门检查

```bash
python run_skill.py lufei-qa -i /tmp/artifact.md -o /tmp/quality_gate.md
```

#### 系统集成检查

```bash
python run_skill.py lufei-integration -i /tmp/system_issue.md -o /tmp/runbook.md
```

### 4. 查看 token 用量

加 `--show-usage` 显示 token 消耗：

```bash
python run_skill.py viral-analysis -i transcript.txt --show-usage
```

### 5. 本地转写音视频（可选）

如果你有视频/音频文件需要转逐字稿（不用小红书"点点"），用 `whisper_transcribe.py`：

```bash
# 装可选依赖（faster-whisper + ctranslate2，首次会下载模型）
pip install -r requirements-transcribe.txt

# 转一条视频，输出纯文本逐字稿
python whisper_transcribe.py 路飞_vol13.mp4 -o transcript.txt

# 输出带时间戳的 SRT
python whisper_transcribe.py video.mp4 -f srt -o subs.srt

# 用大模型（更准但慢，推荐做正式素材分析）
python whisper_transcribe.py video.mp4 --model large-v3 --language zh -o transcript.txt
```

模型尺寸对照：

| 模型 | 大小 | 速度 | 中文短视频准确度 |
|------|------|------|--------|
| tiny | 39M | 最快 | 听个大概 |
| small | 244M | 快 | 可用 |
| **medium** (默认) | 769M | 中 | 推荐 |
| large-v3 | 1.5G | 慢 | 最佳 |

转出来的逐字稿可以直接喂给 `run_skill.py viral-analysis` 拆解：

```bash
python whisper_transcribe.py video.mp4 -o transcript.txt
python run_skill.py viral-analysis -i transcript.txt -o report.md
```

## 路飞知识水电站角色分工

| 角色 | Skill / 能力 | 说明 |
|---|---|---|
| Elon Mask / `lufei-ceo` | `lufei-ops-orchestrator` | 路飞个人微信 DM 入口，拆任务，写 Kanban 验收 |
| Larry Page / `lufei-larry` | `lufei-data-intake` + Hermes 小红书/腾讯会议/有道工具 | 资料提取与 raw 入库 |
| Reed Hastings / `lufei-reed` | `lufei-content-studio` + 四个 xhs skills | 爆款拆解、选题、逐字稿、评论情报 |
| Steve Jobs / `lufei-jobs` | `lufei-service-diagnosis` | 简历、作品集、面试复盘、课程咨询流程 |
| Sam Altman / `lufei-altman` | `lufei-quality-gate` | 引用、反幻觉、人设、交付边界 |
| Satya Nadella / `lufei-satya` | `lufei-system-integration` | Hermes/微信/Kanban/Obsidian 联调 |
| Bezos / `lufei-bezos` | `lufei-member-cs` | 未来客户微信客服入口、CRM、转化线索 |

## 小红书内容 SKILL 协作（Agent-first 视角）

按 ADR-015，工作流不是 pipeline 而是 agent 自主决策：

```
Goal: 给路飞下条爆款逐字稿
      ↓
  Agent 自主决策：
      ↓
  1. 调 viral-analysis 拆参考爆款，默认输出互动动机、留存完播、下一条选题和 script_brief
  2. 调 topic-selection 把 next_topic_seeds 扩展为 50 个候选 → 筛 Top 5 → 用户/路飞选一个
  3. 调 comment-intelligence 深挖评论需求/关键词（如果有评论或评论截图）
  4. 调 script-generation 写稿，同时生成互动设计标注版逐字稿和评论触发设计
  5. 调 viral-analysis 自评刚生成的稿
  6. 如果自评 < 7 分，回到第 4 步迭代
```

当前 `run_skill.py` 是 Phase 4 之前的"单次调用"接口。Phase 4 接 Hermes 后，agent 会自动完成上面的决策。

## 备选用法：直接复制到 Claude / ChatGPT 网页

如果你不想配 API，也可以：

1. 打开任意一个 `skills/*/SKILL.md` 文件
2. 复制从 `# 标题` 开始到末尾的所有内容
3. 粘贴到 Claude/ChatGPT/DeepSeek 网页的对话开头
4. 给它一份输入数据
5. 看输出

## SKILL 质量验证 checklist

每次 SKILL 调优后用这个 checklist 自测：

- [ ] 钩子评分跟你的直觉一致（差距 ≤ 2 分）
- [ ] 爆点定位准确（找出来的句子确实是你认为爆的那句）
- [ ] 可复刻清单可操作（不是 "写好钩子" 这种废话）
- [ ] 不会美化低质量样本（低质量给低分）
- [ ] 严格 cite 原文（不会臆测）
- [ ] 路飞场景的反爆款信号（"X 次觉醒"、"宝宝姐妹"等）能被识别为反例

## 本仓库静态自测

```bash
cd /Users/champion/Documents/develop/skills
python xhs-content-pipeline/tests/static_skill_check.py
python -m py_compile xhs-content-pipeline/run_skill.py xhs-content-pipeline/tests/static_skill_check.py
```

## 路飞知识水电站测试输入

测试 fixture 位于 `xhs-content-pipeline/tests/fixtures/`：

| 文件 | 用途 | 推荐命令 |
|---|---|---|
| `lufei_ops_input.md` | Elon Mask 内部运营编排 | `python xhs-content-pipeline/run_skill.py lufei-ops -i xhs-content-pipeline/tests/fixtures/lufei_ops_input.md` |
| `lufei_content_studio_input.md` | Reed 内容生产包 | `python xhs-content-pipeline/run_skill.py lufei-content -i xhs-content-pipeline/tests/fixtures/lufei_content_studio_input.md` |
| `lufei_member_cs_input.md` | Bezos 客服/CRM | `python xhs-content-pipeline/run_skill.py lufei-cs -i xhs-content-pipeline/tests/fixtures/lufei_member_cs_input.md` |
| `lufei_service_diagnosis_input.md` | Steve Jobs 服务诊断 | `python xhs-content-pipeline/run_skill.py lufei-service -i xhs-content-pipeline/tests/fixtures/lufei_service_diagnosis_input.md` |
| `lufei_quality_gate_input.md` | Sam Altman 质量门 | `python xhs-content-pipeline/run_skill.py lufei-qa -i xhs-content-pipeline/tests/fixtures/lufei_quality_gate_input.md` |
| `lufei_system_integration_input.md` | Satya 系统集成 | `python xhs-content-pipeline/run_skill.py lufei-integration -i xhs-content-pipeline/tests/fixtures/lufei_system_integration_input.md` |

## SKILL 迭代优先级（按改动收益从高到低）

1. **`几个对照例子（few-shot）`** —— LLM 最依赖的部分。补真实拆过的高/中/低案例
2. **`赛道特异性`** —— 针对你的垂类补差异化规则
3. **`行为约束`** —— LLM 经常犯的错就加约束
4. **维度/评分公式** —— 区分度低的维度可考虑删/合
