# 小红书爆款内容生产链路 (xhs-content-pipeline)

针对设计师职业发展 + 大厂求职垂类调优的 AI 辅助内容生产工具链。

## 当前状态

| 模块 | 状态 |
|------|------|
| **拆解 SKILL** (`xhs-viral-analysis` v0.2) | ✅ 已落地，五维框架（钩子/框架/爆点/情绪/阈值） |
| **生成 SKILL** (`xhs-script-generation` v0.1) | ✅ 已落地，视频/图文双骨架 + 8 条反爆款保护 |
| **选题 SKILL** (`xhs-topic-selection` v0.1) | ✅ 已落地，三维评分推荐 |
| **`run_skill.py` 调用脚本** | ✅ 已落地，接 FreeModel API |
| **`whisper_transcribe.py` 转写脚本** | ✅ 已落地，本地 faster-whisper |
| **Hermes Plugin 集成** | ⏸ 待 Phase 4 |
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
├── skills/
│   ├── xhs-viral-analysis/SKILL.md       ← 拆解 v0.2
│   ├── xhs-script-generation/SKILL.md    ← 生成 v0.1
│   └── xhs-topic-selection/SKILL.md      ← 选题 v0.1
├── plugin.yaml                            ← (Phase 4 待建) Hermes 插件清单
└── tools/                                 ← (Phase 4-5 待建)
    ├── transcribe.py                      ← Whisper 转写
    ├── analyze.py                         ← analyze SKILL 调用 wrapper
    └── generate.py                        ← 多模型并行生成
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

#### 生成逐字稿

```bash
python run_skill.py script-generation -i /tmp/vol14_input.md -o /tmp/vol14稿.md
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

## 三个 SKILL 之间的协作（Agent-first 视角）

按 ADR-015，工作流不是 pipeline 而是 agent 自主决策：

```
Goal: 给路飞下条爆款逐字稿
      ↓
  Agent 自主决策：
      ↓
  1. 调 topic-selection 出 3-5 候选 → 用户/路飞选一个
  2. 调 viral-analysis 拆参考爆款（如果上下文还没有）
  3. 调 script-generation 写稿
  4. 调 viral-analysis 自评刚生成的稿
  5. 如果自评 < 7 分，回到第 3 步迭代
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

## SKILL 迭代优先级（按改动收益从高到低）

1. **`几个对照例子（few-shot）`** —— LLM 最依赖的部分。补真实拆过的高/中/低案例
2. **`赛道特异性`** —— 针对你的垂类补差异化规则
3. **`行为约束`** —— LLM 经常犯的错就加约束
4. **维度/评分公式** —— 区分度低的维度可考虑删/合
