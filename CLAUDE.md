# 项目：AI 辅助小红书爆款内容生产

> **给打开本目录的 Claude / Agent**：本文件是项目大脑。每次会话开始读一遍，能立刻进入状态。
> **维护规则**：架构、决策、状态变化时立即更新本文件。本文件晚于代码的状态，即视为过期文件。
> **范围纪律**：本文件**只**覆盖小红书爆款内容生产链路。个人知识库、私域转化、矩阵化、toB 客户定制等都属于**未来扩展**（见 §11），不在当前 CLAUDE.md 范围内。

---

## 1. 项目身份

| 项 | 内容 |
|----|------|
| 项目名 | `xhs-content-pipeline`（小红书 AI 辅助爆款内容生产链路） |
| 工作目录 | `D:\Users\111\Desktop\Project\爱马仕\` |
| 项目主体 | `./xhs-content-pipeline/` |
| 参考代码 | `./hermes-agent-main/`（NousResearch Hermes Agent v0.14.0，作为底层框架） |
| Owner / 开发者 | azan |
| **第一个签约客户** | **路飞设计沉思录**（小红书 [@5f5b897100000000010068c1](https://www.xiaohongshu.com/user/profile/5f5b897100000000010068c1)） |
| 客户画像 | 滴滴/VIPshop 前设计总监；赛道=**设计师职业发展 + 大厂求职**；粉丝 1k+；累计互动 1w+；单篇浏览 50-3500；业务=1v1 辅导 + 大厂设计课；内容形态=**实用干货类** |
| 内容类型分档 | 实用干货类（爆款硬线：**收藏 ≥ 1000**，详见 §3.0） |
| **Deadline** | 1-2 天内"测试通过"（SKILL 跑通 + 可录制逐字稿产出）；爆款实际数据要再等几天发布后才能确认 |
| 当前阶段 | **Phase 1：SKILL 设计 + 待用路飞已有作品验证** |
| 起项日期 | 2026-05-19 |

---

## 2. 目标

### 2.1 主目标

**搭建一套 AI 辅助小红书爆款内容生产链路**，覆盖三阶段闭环：

```
[选题阶段]                      [生产阶段]                     [复盘阶段]
AI 拆解竞品爆款          →   用户基于 AI 稿真人录制     →    AI 分析发布数据
提供选题方向                   AI 不替代录制                   找出预测偏差
输出初版逐字稿                 (保留真人感)                     反哺迭代 SKILL
```

### 2.1.1 Phase A 具体交付物（针对路飞）

为路飞产出**至少 1 条达到爆款阈值的发布内容**（阈值见 §3）。这是"用效果买单"的可验证交付，不是"做一套方法论"。

### 2.1.2 商业模式（详见 ADR-012）

**定制 SKILL + 效果买单**：
- 不同客户配不同 SKILL（赛道、风格、内容形态差异）
- 客户买的是**结果**（爆款），不是方法论
- 路飞是第一个签约客户、也是第一个验证场
- 跨客户的 SKILL 库 / 多租户平台化 → 仍在 §11 未来扩展（先把单客户跑通）

### 2.2 A/B 测试方法论

为了量化验证链路价值，**先跑 Phase A 纯爆款链路**，再考虑 Phase B 知识库增强：

```
Phase A: 纯爆款链路 (当前 CLAUDE.md 范围)
├─ 输入: 竞品爆款视频 + 用户的选题方向
├─ 处理: 拆解 SKILL → 生成 SKILL，不依赖任何个人知识库
└─ 输出: 一条可录制的逐字稿

  ↓ 录制发布后 24-72h，看互动数据

Phase B: 知识库增强 (未来扩展，§11)
├─ 输入: 同 Phase A + 个人知识库
├─ 处理: 同 Phase A，但生成时注入个人风格 / 历史素材
└─ 输出: 同 Phase A 但更"像自己"

  ↓ A/B 对照: Phase B 互动数据 - Phase A 互动数据 = KB 价值
```

**A/B 测试的执行约束**：
- 同一选题方向、同一周内发布、同一发布时段，否则变量太多
- 单次测试 ≥ 3 对（小样本随机性大）
- 评估指标: 互动率（点赞 + 收藏 + 评论 / 浏览数），而非绝对数

### 2.3 核心约束（不可违反）

| 约束 | 缘由 | 影响 |
|------|------|------|
| **Agent-first 设计哲学** | AI Agent 是**引擎贯穿所有环节**，不是某个步骤的"功能添加"；Hermes 本来就是 agent-loop 框架 | 不写硬编码 pipeline 脚本；工作流靠 agent goal + tools 表达；每一步由 agent 在 context 中自主判断；见 ADR-015 |
| **真人感优先** | AI 替代录制会让内容失去人格魅力，违背小红书生态 | AI 只输出"参考稿"，用户必须真人录制 |
| **效果导向（用效果买单）** | 对客户的核心承诺；客户买的是爆款结果，不是方法论 | 项目成功标准 = 至少 1 条达爆款阈值（§3），不是 "SKILL 写完" |
| **本地优先** | 视频音频是敏感原料 | 转写、拆解全部本地完成，不传第三方 |
| **自动发布禁用** | 小红书对发布行为反爬最严，封号代价高 | 发布上线全程手动 |
| **采集合规化** | 直接爬小红书后台风险高，但完全手动又低效 | 用合法 SaaS（灰豚）+ 隔离小号 + 限频抓取（见 ADR-010） |
| **范围纪律** | 防止 scope creep 拖死项目 | 知识库 / 矩阵 / 多客户平台化 全部放 Phase B，当前不写代码 |

### 2.4 非目标（明确排除）

- ❌ 替代真人录制
- ❌ 自动发布到小红书
- ❌ 自动剪辑视频（用户确认现有 AI 剪辑效果差）
- ❌ 小红书内容爬取（合规风险）
- ❌ 替代封面设计（稿定设计无开放 API）
- ❌ **个人知识库 / 私域 / 矩阵 / toB 定制**（全部在 §11 未来扩展，不在当前实现范围）

---

## 3. 系统指标 (KPIs)

> 初稿，待持续迭代。

### 3.0 爆款定义（核心 KPI，按内容类型分档）

小红书爆款阈值矩阵（按内容类型分档，2026-05-19 确定）：

| 内容类型 | 点赞 | 收藏 | 评论 | 备注 |
|------|------|------|------|------|
| 实用干货类（教程/攻略/清单）| ≥ 300 | **≥ 1000** | ≥ 20 | 收藏过千才是硬爆款 |
| 情绪/生活分享类（日常/感悟/美妆穿搭）| ≥ 1000 | ≥ 300 | ≥ 30 | 点赞为主，收藏为辅 |
| 强互动类（投票/求助/争议）| ≥ 500 | ≥ 100 | **≥ 100** | 评论是核心指标 |
| **通用"小爆款"** | ≥ 500 | ≥ 300 | ≥ 20 | 最稳妥的低门槛标准 |
| 通用"大爆款" | ≥ 3000 | ≥ 1000 | ≥ 100 | 小红书真正的全网爆款 |

### 3.0.1 路飞场景的目标定位

路飞内容形态 = **实用干货类**（设计师作品集教程 / 大厂面试攻略 / 求职清单），按上表硬指标**收藏 ≥ 1000** 才算硬爆款。

**分阶段目标**：
1. **Day 1-2 测试通过的标志** = SKILL 拆解 + 生成 SKILL 跑通，产出可录制的逐字稿
2. **首次爆款里程碑 A**（合理首目标）= 命中"**通用小爆款**"线：点赞 ≥ 500、收藏 ≥ 300、评论 ≥ 20
3. **首次爆款里程碑 B**（项目最终交付）= 命中"**实用干货类硬爆款**"线：收藏 ≥ 1000、点赞 ≥ 300、评论 ≥ 20
4. **远期目标** = 大爆款（收藏 ≥ 1000 + 点赞 ≥ 3000）

### 3.1 质量指标

| 指标 | 目标值 | 测量方法 | 现状 |
|------|--------|---------|------|
| 拆解准确度（钩子分） | 与人工评分差距 ≤ 2/10 | 5 条标杆视频盲测 | 待测 |
| 拆解一致性 | 同一逐字稿连续 3 次拆解，关键结论一致 | 重复测试 | 待测 |
| 复刻清单可操作率 | 100% 项可直接落到稿子，无抽象口号 | 人工 review | 待测 |
| 生成稿用户接受度 | ≥ 70%（不大改可用） | 用户标注 | N/A |

### 3.2 效率指标

| 指标 | 目标值 | 测量方法 | 现状 |
|------|--------|---------|------|
| 单条逐字稿转写耗时 | < 30s（5 分钟视频） | Whisper 端到端 | N/A |
| 单条爆款拆解耗时 | < 60s | 从输入逐字稿到输出报告 | N/A |
| 单条逐字稿生成耗时 | < 3 min（含多模型对比 + 选稿） | 端到端 | N/A |
| 链路完整成功率 | > 95% | 100 条样本端到端 | N/A |

### 3.3 业务指标（A/B 测试用）

| 指标 | 含义 | 何时用 |
|------|------|------|
| 单人产能 | AI 介入前 vs 后，单位时间内可产出的逐字稿条数 | Phase A 验证后 |
| 互动率（点赞+收藏+评论）/ 浏览 | AI 辅助的稿 vs 纯人工稿 | A/B 测试 |

---

## 4. 架构

### 4.1 整体分层（Agent-first 架构）

**关键**：没有"工作流编排层"。Agent 是引擎，工作流由 agent 在运行时基于 goal 自己决定调用顺序，不写硬编码 pipeline。

```
┌──────────────────────────────────────────────────────────────────────┐
│  用户层  │  本人（创作者） + 路飞（客户）                              │
└──────────────────────────────────────────────────────────────────────┘
                                ↓ Goal: "给路飞做条爆款逐字稿..."
┌──────────────────────────────────────────────────────────────────────┐
│  入口层  │  Hermes CLI / TUI （+ 消息平台网关，可选）                 │
│         │  仅传递 goal，不预定义步骤                                    │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
╔══════════════════════════════════════════════════════════════════════╗
║  ★ AGENT 核心（引擎） ★    Hermes AIAgent (run_agent.py:326)         ║
║                                                                       ║
║  - conversation_loop: 每次循环判断"还缺什么、调哪个工具、是否够好"      ║
║  - context_engine: 在多轮中保持 context                                ║
║  - memory_manager: 跨会话记忆                                          ║
║                                                                       ║
║  Agent 决策模式（每一步自问）：                                          ║
║   1. 当前 context 够不够推进 goal?                                    ║
║   2. 缺哪类数据? 哪个工具能补?                                         ║
║   3. 输出质量够不够? 要不要再迭代?                                      ║
║   4. 现在的判断要不要先跟用户确认?                                       ║
╚══════════════════════════════════════════════════════════════════════╝
                ↓ (按需自主调用，不预定义顺序)                  ↑ 结果回流
┌──────────────────────────────────────────────────────────────────────┐
│  能力池 (Skills + Tools + Knowledge)                                  │
│                                                                       │
│  Skills (Agent 看的领域知识 / 决策框架):                                │
│    选题 ✅ │ 拆解 ✅ (v0.3.2 严格反胡编) │ 生成 ✅ │ 复盘(待建)         │
│                                                                       │
│  Tools (Agent 能调的执行能力):                                          │
│    whisper_transcribe │ analyze │ generate │ review │                 │
│    huitun_collector │ xhs_video_downloader                            │
│                                                                       │
│  Knowledge (Agent 能查的事实):                                          │
│    路飞画像 │ 历史互动数据 │ 爆款阈值矩阵(§3.0) │ LMVK(Phase B)         │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│  模型层 │ Claude / DeepSeek / Gemini / 豆包（待加）                    │
│        │  via OpenRouter / FreeModel 中转（见 §12）                    │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│  存储层                                                                │
│  - Hermes 会话 / 配置: ~/.hermes/  (SQLite + FTS5)                    │
│  - 项目素材: ./videos/ ./transcripts/ ./reports/                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 当前已实现

| 组件 | 路径 | 状态 |
|------|------|------|
| 项目骨架 | `./xhs-content-pipeline/` | ✅ |
| 拆解 SKILL **v0.3.2** | `./xhs-content-pipeline/skills/xhs-viral-analysis/SKILL.md` | ✅ v0.3 引入 CES 算法权重 + 2 小时窗口 + 第六维"关注转化暗示"+ 爆点主驱动 + CES 阈值矩阵 + 互动质量诊断；**v0.3.2 严格反胡编模式**（撤销 v0.3.1 元数据推断路径，缺正文/转写时禁止脑补钩子六维/框架/情绪曲线，只允许 CES + 互动诊断硬数据计算，见 ADR-018）|
| **xhs-pipeline Hermes Plugin** | `./xhs-content-pipeline/plugin.yaml` + `__init__.py` | ✅ 注册 3 个 huitun_* tool（search/hot/collect_my），junction 到 `~/.hermes/plugins/xhs-pipeline/`；agent 可在 hermes 里调用，端到端 CLI + 微信验证通过 |
| **Hermes 本地安装** | `C:\Users\111\AppData\Local\hermes\` | ✅ v0.14.0 (2026.5.16) + 7 commits update；DeepSeek V4 Flash via `api.deepseek.com` 直连（key 在 config.yaml）；3 个 xhs SKILL junction 到 `~/.hermes/skills/` |
| **Weixin Gateway**（ClawBot, Bonus 不在原 TODO）| `~/.hermes/weixin/accounts/884e75d05c76@im.bot.json` | ✅ hermes gateway setup 扫码绑定，iLink Bot API；DM pairing approval 启用；Scheduled Task 开机自启；端到端在微信里调 huitun + viral-analysis 跑通（见 ADR-019）|
| **Agent 自动落盘报告**（端到端验证产物）| `./xhs-content-pipeline/reports/{viral-analysis,topic-selection,script-generation}-*.md` | ✅ 3 SKILL 接力测试 agent 自主决定保存的报告（agent-first 哲学最佳实战）；vol.14 字节作品集面试稿预期 CES 7296，比 vol.13 +20% |
| **生成 SKILL v0.2** | `./xhs-content-pipeline/skills/xhs-script-generation/SKILL.md` | ✅ 引入 CES 三件触发器（关注转化 + 评论 prompt + 转发钩子）强制内置；路飞 vol.14 初稿 CTA 段已按 CES 三件重写；预期 CES 提升 21% |
| **选题 SKILL v0.1** | `./xhs-content-pipeline/skills/xhs-topic-selection/SKILL.md` | ✅ 三维度评分（博主匹配 0.4 + 热度 0.4 + 可执行 0.2）+ 路飞 4 个已评分候选选题 + 反爆款选题信号 |
| **`run_skill.py` 调用脚本** | `./xhs-content-pipeline/run_skill.py` | ✅ 单次原子调用任意 SKILL，接 FreeModel API，不依赖 Hermes |
| **`whisper_transcribe.py` 转写脚本** | `./xhs-content-pipeline/whisper_transcribe.py` | ✅ 本地 faster-whisper 音视频转写（plain/srt/json 输出），不依赖 Hermes 不依赖 API |
| 依赖清单（核心） | `./xhs-content-pipeline/requirements.txt` | ✅ openai + python-dotenv |
| 依赖清单（转写可选） | `./xhs-content-pipeline/requirements-transcribe.txt` | ✅ faster-whisper |
| API 配置模板 | `./xhs-content-pipeline/.env.example` | ✅ FreeModel 双格式配置示例 |
| 项目导览 | `./xhs-content-pipeline/README.md` | ✅ 含 run_skill.py 使用说明 |
| 本文件 | `./CLAUDE.md` | ✅ |

### 4.3 待实现（按优先级）

| 组件 | 路径（计划） | 阶段 | 阻塞 |
|------|------|------|------|
| 复盘 SKILL | `skills/xhs-performance-review/SKILL.md` | Phase 6 | 有发布数据后 |
| Plugin 骨架 | `plugin.yaml` + `__init__.py` | Phase 4 | Hermes 安装完毕 |
| Tool: whisper_transcribe | `tools/transcribe.py` | Phase 4 | 同上 |
| Tool: analyze | `tools/analyze.py` | Phase 4 | 同上 |
| **Tool: huitun_collector**（灰豚 Playwright 采集） | `tools/collectors/huitun.py` | Phase 4 | 同上 + 用户准备灰豚账号 |
| **Tool: xhs_video_downloader**（研究小号下视频） | `tools/collectors/xhs_video.py` | Phase 4 | 同上 + 用户准备研究小号 |
| Tool: generate | `tools/generate.py` | Phase 5 | 同上 |
| Tool: review | `tools/review.py` | Phase 6 | 同上 |
| CLI 命令 | `hermes xhs run ...` / `collect ...` | Phase 5 | 同上 |
| 豆包 provider plugin | `plugins/model-providers/doubao/` | Phase 5 | 拿到豆包 API key |

---

## 5. 三阶段工作场景（**Agent Goals，非 Pipeline**）

> **设计原则**：以下不是"步骤流程图"，是给 Agent 看的"目标声明 + 可用能力"。Agent 在 context 里读到 goal 后，**自主决定**调用哪些工具、按什么顺序、何时回查用户。我们不写硬编码的 `pipeline.run()`。
>
> 这跟传统脚本工程的根本区别：
> - 脚本：人写流程图 → 代码照执行
> - Agent：人给目标 + 能力清单 → agent 自行 reason 怎么达成

### 5.1 选题场景

**Agent Goal 示例**：
> "我要为路飞下一周的发布选 3 个选题方向。路飞赛道=设计师职业发展+大厂求职，内容形态=实用干货类。本周设计垂类的爆款共性是什么？哪些选题路飞做能爆？"

**Agent 可用能力**：
- Tools: `huitun_collector`、`xhs_video_downloader`、`whisper_transcribe`
- Skills: `xhs-viral-analysis`（拆解）、`xhs-topic-selection`（待建）
- Knowledge: 路飞历史互动 / §3.0 爆款阈值 / 赛道特异性规则

**Agent 自主决策的典型路径**（仅示例，不是硬规定）：
1. 先看本地有没有近期的爆款拆解缓存？没有则去采集
2. 调灰豚拉近期 Top → 调小号下视频 → whisper 转写 → 拆解 SKILL
3. 拆解结果聚类 → 用选题 SKILL 给出 3 个方向
4. **如果中途数据不够（比如灰豚导不出来），自己降级**：用人工 URL 兜底 / 跟用户确认要不要换方案
5. 最终交付前自查：3 个方向是不是真的差异化？路飞画像匹配吗？

> Phase 1-2 阶段：采集 tool 还没实现，agent 退化为"用户喂逐字稿→直接拆"。这本身也是 agent 自主判断的体现（能力不全时降级，而不是报错卡死）。

### 5.2 生产场景

**Agent Goal 示例**：
> "用选题方向 X + 这份拆解报告 Y，给路飞产出一条预期能命中实用干货类爆款（收藏≥1000）的逐字稿。多模型对照后给出最终版 + 备选 + 你的判断依据。"

**Agent 可用能力**：
- Tools: `generate`（多模型并行 wrapper）
- Skills: `xhs-script-generation`（待建）
- Knowledge: 路飞文风样本 / 拆解报告 / 钩子和爆点模板库

**Agent 自主决策的典型路径**：
1. 读拆解报告，识别选题对应的钩子类型 + 框架模板
2. 决定调几个模型对照（DeepSeek / Gemini / 豆包）
3. 并行 generate，拿到 3 版稿
4. 对每版自评：钩子分 / 爆点强度 / 是否像路飞
5. 如果都没达预期，**主动迭代或追问用户**（"我觉得几版钩子都偏弱，要不换个方向？"）
6. 输出最终稿 + 自评报告

### 5.3 复盘场景

**Agent Goal 示例**：
> "路飞发布的这条数据出来了（点赞 X / 收藏 Y / 评论 Z），帮我对比拆解阶段的预测，找偏差，给出 SKILL 的待优化项。"

**Agent 可用能力**：
- Tools: `review`（待建）、`session_search`（查历史拆解报告）
- Skills: `xhs-performance-review`（待建）
- Knowledge: §3.0 阈值矩阵 / 历史拆解预测 / 路飞过往表现

**Agent 自主决策的典型路径**：
1. 在会话历史里找出当时的拆解报告 + 生成时的预测
2. 跟实际数据对比，识别偏差最大的维度（钩子？爆点？情绪节奏？）
3. 抓评论内容找用户真实反应
4. 提议 SKILL 的具体修改点（不是"加强钩子"，而是"把模板 X 改成 Y"）
5. 询问用户授权后落到 SKILL 文件

---

## 6. 关键决策记录 (ADR)

| ID | 决策 | 日期 | 理由 |
|----|------|------|------|
| ADR-001 | 选 Hermes Agent 作为底层框架 | 2026-05-19 | 自学习闭环、多模型抽象、本地优先架构都对路；MIT 开源 |
| ADR-002 | **拆分原"不爬不发"为两条**：发布禁用 / 采集合规化 | 2026-05-19 | 原一刀切过于保守，手动 URL 效率不足；采集和发布的封号风险分级不同，应分别治理 |
| ADR-003 | 转写不用小红书"点点"，用 faster-whisper | 2026-05-19 | "点点"无 API；faster-whisper 本地可控 |
| ADR-004 | SKILL 优先用 Markdown，不写代码 | 2026-05-19 | 提示词工程产物本质就是文档，便于迭代 |
| ADR-005 | 所有自定义能力走 plugin，不动 hermes 核心 | 2026-05-19 | `hermes-agent-main/AGENTS.md:531` 明确禁止改核心 |
| ADR-006 | 拆解框架升级为"互动三轴" | 2026-05-19 | 结合"开头 / 收藏 / 争议"三要素扩展，原 SKILL 缺评论轴 |
| ADR-007 | Phase A 不依赖个人知识库 | 2026-05-19 | 采用 A/B 测试方法论：先跑纯爆款链路再加 KB 做对照，量化 KB 增益 |
| ADR-008 | CLAUDE.md 范围收窄到小红书爆款生产链路 | 2026-05-19 | 为防止 scope creep：知识库 / 私域 / 矩阵 / toB 全部归入 §11 未来扩展，不在本文件范围 |
| ADR-009 | 不引入 OpenMontage | 2026-05-19 | 经评估，OpenMontage 是 AI 端到端**生成**视频系统（TTS / AI avatar / AI 视觉），与"真人感优先"约束直接冲突；其 12 pipeline 无一覆盖"从社交平台采集分析"场景 |
| ADR-010 | 采集方案：灰豚 SaaS + 研究小号 + Playwright | 2026-05-19 | 灰豚是小红书数据平台中"性价比 + 免费试用"最优的；纯爬虫法律灰色 + 维护痛；用户日常账号封号代价高，故隔离一个研究小号专门用于视频下载 |
| ADR-011 | **签约客户路飞作为 Phase A 试验场** | 2026-05-19 | 路飞 = 设计师职业发展赛道，有大厂背书但还没爆过，是真实从 0 到 1 的突破挑战。所有 SKILL 调优用路飞的实际数据，不用泛样本 |
| ADR-012 | **商业模式：定制 SKILL + 效果买单** | 2026-05-19 | 不同客户配不同 SKILL；客户买的是爆款，不是方法论。这是单客户级别的客户定制（不是多租户平台），不冲突 ADR-008 |
| ADR-013 | **爆款必须有量化定义** | 2026-05-19 | 爆款必须用"物理特征"（点赞/收藏/评论）量化界定，不能凭感觉。具体阈值见 §3.0；针对设计垂类做了 weighted 调整（收藏率 > 点赞率） |
| ADR-014 | **LMVK = LLM Wiki（结构化 Markdown 知识库）** | 2026-05-19 | 术语定义。LMVK 是 Phase B 的事，当前不实现。路飞的素材（模拟面试视频 / 培训课程录像 / 印象笔记 / 有道笔记）以后按此方式整理 |
| ADR-015 | **Agent-first 设计哲学：AI Agent 是引擎，不是 pipeline 中的一个节点** | 2026-05-19 | AI Agent 是引擎贯穿所有环节，不是某个步骤的功能添加。原 §5 工作流写成流程图式，是错的方向。Hermes 本来就是 agent-loop 框架。本项目不写硬编码 `pipeline.run()`，工作流靠 agent 在 context 中读 goal + 自主调 tools 实现。所有"流程"描述改写为"agent goal + 可用能力 + 决策模式" |
| ADR-016 | **不引入 OpenHuman 到 Phase A，留作 Phase B 候选** | 2026-05-19 | 经评估，OpenHuman 是个人长期记忆 AI agent（Memory Tree + 118 服务 OAuth + 80% token 压缩），定位是"做你的 KB"，不是"做内容拆解 / 生成"。当前 Phase A 是内容工程，Hermes 更对。Phase B 路飞 LMVK 时再评估 OpenHuman 是否作为 KB 实现方案 |
| ADR-017 | **LLM 中转 = FreeModel（Anthropic + OpenAI 双格式）** | 2026-05-19 | `https://cc.freemodel.dev`(Anthropic) + `https://api.freemodel.dev`(OpenAI)，支持 tool calling。Phase 4 接 Hermes 时作为默认 provider；后期视稳定性再决定要不要备双源 |
| ADR-018 | **SKILL v0.3.2 严格反胡编模式**：撤销 v0.3.1 "huitun 元数据 → 推断钩子六维评分" 路径 | 2026-05-22 | v0.3.1 引入 huitun 元数据推断后, agent 在缺正文/视频转写时会基于标题脑补钩子六维评分 / 框架 / 情绪曲线，违反 §8.1「必须 cite 原文」。v0.3.2 限制元数据模式只输出 CES + 互动诊断（数学计算），严禁推断五维分析；agent 必须主动建议调 xhs_extract_note 或 whisper_transcribe 补充内容输入。**反向验证通过**：纯元数据输入时 agent 输出 `[硬数据模式]` 拒绝脑补 |
| ADR-019 | **Weixin gateway 走 Hermes 原生 iLink Bot API**（取代外部 MCP 方案）| 2026-05-22 | Hermes v0.14.0+7commits 原生支持腾讯 iLink Bot API（仅个人微信号、私聊，群聊基本不投递）。`hermes gateway setup` 扫码绑定后 hermes 可在微信里被 @ 收消息+回复。session 约 2-3 小时过期需重 setup（iLink 限制）。完全够 Phase A 单客户场景；放弃了之前考虑的"复用 Claude Code 的 wechat MCP" 方案 |
| ADR-020 | **xhs-pipeline plugin 装载用 junction（不走 GitHub）** | 2026-05-22 | `hermes plugins install` 只接 Git URL/owner/repo，但开发期反复改代码不适合 push-install 循环。改用 Windows junction（`mklink /J`）把 `xhs-content-pipeline\` 链到 `~/.hermes/plugins/xhs-pipeline\`，hermes 启动自动识别为 user plugin，`hermes plugins enable xhs-pipeline` 即生效。改代码立刻生效（无需重新 install），同时保留以后推 GitHub 选项 |
| ADR-021 | **视频解析 tool 由用户自接，本项目不实现 xhs_video_downloader** | 2026-05-22 | 用户已有现成视频解析工具会接入；本项目 Phase 4.5 (xhs_video_downloader) 放弃，避免重复造轮子 + 规避研究小号反爬维护成本。Plugin 只负责采集（huitun_*）和 SKILL 调用，视频内容由用户外部喂入；保持 ADR-015 agent-first 原子能力组合 |

---

## 7. 文件结构

```
D:\Users\111\Desktop\Project\爱马仕\
├── CLAUDE.md                          ← 本文件，项目大脑
├── hermes-agent-main\                 ← Hermes 源码（参考，不要改）
│   ├── AGENTS.md                      ← Hermes 官方开发指南，必读
│   ├── run_agent.py:326               ← AIAgent 类
│   ├── tools\registry.py              ← 工具注册中心
│   ├── plugins\                       ← 插件参考实现
│   └── skills\                        ← 内置 skill 参考
└── xhs-content-pipeline\              ← 项目主体
    ├── README.md                      ← 项目导览 + SKILL 验证指引
    ├── plugin.yaml                    ← (待建) Hermes 插件清单
    ├── __init__.py                    ← (待建) Plugin 入口
    ├── skills\
    │   ├── xhs-viral-analysis\
    │   │   └── SKILL.md              ← ✅ 拆解 SKILL v1
    │   ├── xhs-topic-selection\      ← (待建)
    │   ├── xhs-script-generation\    ← (待建)
    │   └── xhs-performance-review\   ← (待建)
    ├── tools\                         ← (待建)
    │   ├── transcribe.py
    │   ├── analyze.py
    │   ├── generate.py
    │   ├── review.py
    │   └── collectors\
    │       ├── huitun.py              ← 灰豚 Playwright 采集
    │       └── xhs_video.py           ← 研究小号下视频
    ├── workflows\                     ← (待建)
    │   └── full_pipeline.py
    └── tests\                         ← (待建) 标杆测试集
        ├── transcripts\               ← 已标注的爆款逐字稿
        └── expected\                  ← 人工拆解的标准答案
```

---

## 8. 开发约定

### 8.1 SKILL 设计原则
1. **不写代码**，全部 Markdown
2. **必须 cite 原文**：分析任何内容必须引用原始片段，禁止臆测
3. **必须可操作**：所有"建议"必须落到具体动作，不要抽象口号
4. **必须打分量化**：避免"挺好的"这种模糊判断
5. **必须含 few-shot 例子**：每个 SKILL 至少 3 个对照案例（高/中/低）

### 8.2 Tool 实现规范（Hermes 接口）

```python
# 真实接口参考: hermes-agent-main/AGENTS.md:263
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("REQUIRED_KEY"))

def my_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})  # 必须返回 JSON 字符串

registry.register(
    name="my_tool",
    toolset="xhs",                     # 我们项目统一用 "xhs" toolset
    schema={...},                       # OpenAI function-calling schema
    handler=lambda args, **kw: my_tool(...),
    check_fn=check_requirements,
    requires_env=["REQUIRED_KEY"],
)
```

### 8.3 文件命名
- SKILL：`skills/<kebab-case-name>/SKILL.md`
- Tool：`tools/<snake_case>.py`
- 测试样本：`tests/transcripts/<日期>_<赛道>_<等级>.txt`（如 `20260519_perfume_high.txt`）

### 8.4 与 Claude 协作的约定
- **不要替我下决定**：架构、SKILL 框架、工具选型等关键决策必须问我
- **每次会话开头确认当前 Phase**：从本文件 §4.2 / §4.3 / §9 看
- **改 SKILL 之前先解释变化**：让我看到 diff 思路再动手
- **不要主动安装 Hermes**：等我授权
- **不要主动连接外部 API**：等我提供 key 和明确授权
- **范围纪律**：超出 §1 主题（小红书爆款内容生产）的事，先指向 §11 未来扩展，再问要不要单独立项

### 8.5 Agent-first 原则（重要，见 ADR-015）

实现工作流时，**不允许**写下面这种代码：

```python
# ❌ 禁止：硬编码 pipeline
def run_pipeline(niche):
    videos = collect_huitun(niche)
    transcripts = [whisper(v) for v in videos]
    analyses = [analyze(t) for t in transcripts]
    topics = select_topics(analyses)
    return topics
```

**允许**的形态是：

```python
# ✅ 正确：agent 自主决策
result = agent.chat(f"""
我要为路飞选 {n} 个本周的爆款选题方向，赛道={niche}。
可用工具：huitun_collector, whisper_transcribe, analyze, ...
可用 SKILL：xhs-viral-analysis, xhs-topic-selection
路飞画像：{persona}

你自主决定调用顺序和数量；中途数据缺失时降级或追问。
""")
```

**判断标准**：如果工作流逻辑是"if A then call B else call C"用 Python 写出来的，那就是 pipeline，不对。如果是用自然语言写在 prompt 里让 agent 判断，那就是 agent-first。

**Tool 的设计也要遵循**：每个 tool 是**单一原子能力**（"采集"、"转写"、"拆解"），不要写"end-to-end pipeline tool"。组合由 agent 完成。

---

## 9. 当前 TODO（按优先级）

按 Phase 组织，**前 3 个 Phase 都不需要安装 Hermes**。

### Phase 1: 拆解 SKILL 针对路飞调优（当前，Day 1 任务）
| # | 任务 | 状态 | 负责 | 时间 |
|---|------|------|------|------|
| 1.0 | 给 SKILL 补"设计/职场实用干货类"赛道特异性章节 + 替换爆款定义为 §3.0 矩阵 | ✅ 完成（合并到 v0.2 升级） | Claude | - |
| 1.1 | 用**路飞的 3 条作品**（高/低互动）做拆解验证 | ✅ 完成 | 用户给文字稿，Claude 拆 | - |
| 1.2 | 用同类设计/求职垂类**爆款博主**作品 2 条做拆解验证（对照组） | ✅ 完成（5.5w 收藏巨爆款 + 8 赞流水） | 用户给文字稿，Claude 拆 | - |
| 1.3 | 根据 1.1+1.2 结果迭代 SKILL（加 few-shot、调维度） | ✅ 完成（合并到 v0.2） | Claude | - |
| 1.4 | SKILL v0.2：加入"互动三轴" + §3.0 矩阵 + 沉浸式钩子 + 情境再现框架 + 图文笔记适配 | ✅ 完成 | Claude | - |

### Phase 2: 生成 SKILL + 路飞首稿（Day 2 任务）
| # | 任务 | 状态 | 负责 | 时间 |
|---|------|------|------|------|
| 2.0 | 设计生成 SKILL `xhs-script-generation`（针对实用干货类，含路飞 vol.14 完整 few-shot） | ✅ 完成 | Claude | - |
| 2.1 | 跟路飞/用户对齐选题方向（默认推荐 vol.14 字节作品集深挖面试） | ⏸ | 用户 + 路飞 | 30 分钟 |
| 2.2 | 用生成 SKILL 产出路飞**第一条可录制逐字稿**（如果 2.1 确认 vol.14，则 few-shot 例 1 就是初稿） | ⏸ | Claude（用户授权后） | 1 小时 |
| 2.3 | 路飞 review，迭代到他认可 | ⏸ | 路飞 + Claude | 1 轮 = 1 小时 |
| 2.4 | **Day 1-2 测试通过的判定**：路飞认可逐字稿 + Claude 给出"为什么这条预期能爆"的 SKILL 报告 | ⏸ | 用户 | - |

### Phase 3: 路飞录制 + 发布 + 数据回看（Day 3+，超出我能控制范围）
| # | 任务 | 状态 | 负责 |
|---|------|------|------|
| 3.1 | 路飞录制 + 剪辑 + 封面 + 发布 | ⏸ | 路飞 |
| 3.2 | 发布后 48-72h 数据沉淀 | ⏸ | 等 |
| 3.3 | 用 §3.0 阈值判定爆款达成情况 | ⏸ | 用户 |
| 3.4 | 不达爆款 → 复盘 SKILL 哪里偏差 → 迭代 | ⏸ | Claude + 用户 |

### Phase 4: 工程化（SKILL 自动化调用 + Hermes Plugin）
| # | 任务 | 状态 | 负责 | 前置 |
|---|------|------|------|------|
| 4.0a | **`run_skill.py` 单次调用 CLI**（FreeModel 直连，不依赖 Hermes） | ✅ 完成 | - | - |
| 4.0b | 安装 Hermes，跑通 hello world | ✅ 完成 (2026-05-22) | 用户 | - |
| 4.1 | Plugin 骨架（plugin.yaml + `__init__.py`） | ✅ 完成 (2026-05-22, xhs-pipeline plugin) | Claude | - |
| 4.2a | **`whisper_transcribe.py` 单次转写 CLI**（faster-whisper 本地） | ✅ 完成 | - | - |
| 4.2b | Tool: `whisper_transcribe`（包成 Hermes tool） | 🚫 取消 (用户接外部视频解析工具，见 ADR-021) | Claude | - |
| 4.3 | Tool: `analyze`（把 run_skill.py 包成 Hermes tool） | ✅ 完成 (3 个 SKILL 直接 junction 到 ~/.hermes/skills/ 给 agent 用) | Claude | - |
| 4.4a | **`huitun_collect.py` 采集 CLI 骨架** | ✅ 完成 | Claude | - |
| 4.4b | explore 灰豚 UI + 填实 search selector | ✅ 完成 (URL 抽取 10/10 成功率) | Claude | - |
| 4.4c | Tool: `huitun_collector`（包成 Hermes tool） | ✅ 完成 (2026-05-22, 3 tool: search/hot/collect_my) | Claude | - |
| 4.5 | Tool: `xhs_video_downloader`（研究小号下视频） | 🚫 取消 (见 ADR-021) | - | - |
| **4.6** | **Weixin gateway 接入**（hermes gateway setup + iLink 扫码 + DM pairing） | ✅ 完成 (2026-05-22, Bonus 不在原 TODO，见 ADR-019) | Claude + 用户 | - |
| **4.7** | **SKILL v0.3.2 严格反胡编升级** | ✅ 完成 (2026-05-22, Bonus 不在原 TODO，见 ADR-018) | Claude | - |
| **4.8** | **3 SKILL 接力调用验证 + reports/ 自动落盘** | ✅ 完成 (2026-05-22, 端到端 agent-first 实战胜利) | Claude | 4.1-4.7 |

### Phase 5: 多模型生成 + CLI 串联
| # | 任务 | 状态 | 负责 |
|---|------|------|------|
| 5.1 | Tool: `generate`（多模型并行 + 选稿） | ⏸ | Claude |
| 5.2 | CLI 命令: `hermes xhs collect`, `hermes xhs run` | ⏸ | Claude |
| 5.3 | 豆包 provider plugin（如果有 API key） | ⏸ | Claude（API key 就绪后） |

### Phase 6: 复盘闭环
| # | 任务 | 状态 | 负责 |
|---|------|------|------|
| 6.1 | 设计复盘 SKILL `xhs-performance-review` | ⏸ | Claude |
| 6.2 | Tool: `review`（包装复盘 SKILL） | ⏸ | Claude |

---

**Day 1-2 关键路径**：Phase 1.0 → 1.1 → 1.2 → 1.3 → 1.4 → 2.0 → 2.1 → 2.2 → 2.3 → 2.4。**全程纯 prompt 工程，不装 Hermes**。

**Day 1-2 起步素材需求**：路飞 3-5 条作品的 URL（或直接文字稿）+ 同赛道大 V 3 条对照作品。素材就位即可启动拆解。

**关于灰豚 + 小号自动化 + Hermes**：是 Phase 4 的事，**不要在 Phase 2-3 跑通前启动**。早做会摊薄精力且无法在没有 SKILL v2 + 生成 SKILL 的情况下闭环价值。Day 1-2 完全用人工 URL/文字稿就够。

---

## 10. 待定的开放问题

| # | 问题 | 选项 | 我的建议 |
|---|------|------|---------|
| Q1 | ~~你做的小红书赛道是哪个？~~ | ✅ 已答：路飞 = 设计师职业发展 / 大厂求职 | - |
| Q2 | A/B 测试 #1 的选题方向有候选吗？ | - | 路飞的素材里挑一个，"大厂面试常见题" / "作品集硬伤盘点" 之类 |
| Q3 | 多模型对比要不要全部用？还是先 DeepSeek + Gemini 两家？ | - | 先两家更聚焦 |
| Q4 | 系统指标 §3 的效率目标值你有调整意见吗？ | - | - |
| Q5 | ~~爆款阈值~~ | ✅ 已确定：按内容类型分档阈值矩阵，路飞按"实用干货类"档。详见 §3.0 | - |
| Q6 | 灰豚账号 + 研究小号什么时候准备？ | Phase 2 跑通后 / 现在就准备好 / 等用到再说 | 不急，Phase 4 才用到 |
| **Q7** | **路飞已发布作品里，互动最高的 3 条 + 最低的 3 条 URL（或直接文字稿）** | - | **Day 1 起步关键素材** |
| **Q8** | **路飞认可的同赛道爆款博主作品 3 条 URL（或文字稿）** | - | **Day 1 起步关键素材** |
| Q9 | ~~项目 deadline~~ | ✅ 已确定：1-2 天测试通过 | - |
| **Q10** | **"测试通过"的具体定义** | A: SKILL 跑通 + 可录制逐字稿（Day 2 可达） / B: 真实爆款数据（Day 5+ 才可能）/ C: 看情况 | 需要对齐预期，避免承诺翻车 |

---

## 11. 未来扩展（**不在当前 CLAUDE.md 范围**，只做指针）

以下议题已识别，但**当前项目不涉及具体实现**。等 Phase A 跑通后再讨论是否立项：

| 议题 | 关联 | 当前态度 |
|------|------|---------|
| **Phase B：路飞 LMVK（LLM Wiki 知识库）+ 内容定制化** | A/B 测试方法论后半段 | 等 Phase A 跑通至少 1 条爆款后启动；素材包括路飞模拟面试视频 / 培训课程录像 / 印象笔记 / 有道笔记 |
| 知识库技术选型（向量库 / GraphRAG / 纯 Markdown + grep / **OpenHuman**） | 见 ADR-016 | LMVK 启动时一起决定。**OpenHuman**（[tinyhumansai/openhuman](https://github.com/tinyhumansai/openhuman)）是强候选：Memory Tree (Markdown+SQLite, Obsidian 兼容) + 118 服务 OAuth + 80% token 压缩，正好对路 LMVK 场景。但当前 Phase A 不引入，见 ADR-016 |
| 私域转化策略（公众号 / 微信 / 用户生命周期） | 运营议题 | 非本项目范围 |
| 矩阵化运营（主 + 副账号） | 运营议题 | 等单账号跑通再讨论 |
| **多客户 SKILL 平台化**（不同客户不同 SKILL 的工程化承载） | 见 ADR-012 | 等 ≥ 2 个客户后再讨论平台化；路飞单客户跑通前不做 |

> 如果会话中出现这些议题，先指向本节，确认用户是要"在本项目内做"还是"另立项目"，不要默认开始实现。

---

## 12. 联系信息 / 参考资料

### 项目内
- 项目内导览: [xhs-content-pipeline/README.md](xhs-content-pipeline/README.md)
- 当前 SKILL: [xhs-content-pipeline/skills/xhs-viral-analysis/SKILL.md](xhs-content-pipeline/skills/xhs-viral-analysis/SKILL.md)

### Hermes 框架
- Hermes 官方文档: https://hermes-agent.nousresearch.com/docs/
- Hermes 开发指南: [hermes-agent-main/AGENTS.md](hermes-agent-main/AGENTS.md)

### 可用 LLM 端点（见 ADR-017）
- **FreeModel 中转**（用户的账号）
  - Anthropic 格式：`https://cc.freemodel.dev`（可给 Claude Code / Hermes anthropic plugin 用）
  - OpenAI 格式：`https://api.freemodel.dev`（兼容 ChatGPT SDK / Hermes openai-compatible）
  - 支持：tool calling、流式、图片识别、扩展思考
  - 用户层级：t0（claude-t0 / 默认线路）；T1+ 需充值解锁
- 备用：OpenRouter（200+ 模型聚合，Phase 4 接 Hermes 时考虑）

### Phase B 候选（不在当前范围）
- OpenHuman: https://github.com/tinyhumansai/openhuman （Phase B 知识库候选，见 ADR-016）

---

**Last updated**: 2026-05-22 by Claude — Hermes 安装 + xhs-pipeline plugin 跑通 (4.1/4.4c) + Weixin gateway 接入 (4.6, ADR-019) + SKILL v0.3.2 严格反胡编 (4.7, ADR-018) + 3 SKILL 接力链路验证 (4.8). agent 自主落盘 3 份报告在 `xhs-content-pipeline/reports/`. ADR-020 (junction 装载) + ADR-021 (取消自建视频下载) 收尾决策记录在案
**Next review**: 路飞跑出第一条达爆款阈值的内容后；或下次接入视频解析工具时
