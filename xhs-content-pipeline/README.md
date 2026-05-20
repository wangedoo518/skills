# 小红书内容生产链路 (xhs-content-pipeline)

基于 Hermes Agent 搭建的小红书短视频内容生产工作链路。

## 当前阶段

📍 **Stage 1：SKILL 设计阶段** — 已完成 `xhs-viral-analysis`（爆款拆解）

下一步规划：
- [ ] Stage 2：手动验证 SKILL 的拆解质量（**当前推荐做的**）
- [ ] Stage 3：写 `xhs-script-generation` SKILL（逐字稿生成）
- [ ] Stage 4：安装 Hermes，搭 Plugin 骨架
- [ ] Stage 5：实现 `whisper_transcribe` 工具（音频→逐字稿）
- [ ] Stage 6：实现 `analyze_viral_content` 工具（包装 SKILL 调用）
- [ ] Stage 7：实现 `generate_my_script` 工具（多模型并行）
- [ ] Stage 8：注册 CLI 命令 `hermes xhs run --input ...`，串成 workflow

## 目录结构

```
xhs-content-pipeline/
├── README.md                   ← 你正在看的文件
├── plugin.yaml                 ← (待创建) Hermes 插件清单
├── __init__.py                 ← (待创建) 插件入口
├── skills/
│   └── xhs-viral-analysis/
│       └── SKILL.md            ← ✅ 已完成
└── tools/                      ← (待创建)
    ├── transcribe.py           ← Whisper 转写
    ├── analyze.py              ← 拆解工具
    └── generate.py             ← 多模型生成
```

## 如何在 Hermes 装好之前就用 SKILL

**SKILL 本质是结构化提示词**，完全可以脱离 Hermes 单独验证：

### 方式 A：直接复制到 ChatGPT/Claude/DeepSeek 网页

1. 打开 `skills/xhs-viral-analysis/SKILL.md`
2. 复制**从 `# 小红书爆款拆解` 开始到末尾**的全部内容
3. 粘贴到对话开头
4. 粘贴一份小红书逐字稿
5. 观察输出是否符合预期

### 方式 B：通过 API 验证（推荐用 Python 脚本）

如果你有 OpenAI/Claude/DeepSeek 的 API key，可以写个小脚本：

```python
import openai  # 或 anthropic
client = openai.OpenAI(api_key="sk-...")

with open("skills/xhs-viral-analysis/SKILL.md", encoding="utf-8") as f:
    skill = f.read()

transcript = """
我不允许还有人不知道这个 19 块钱的神器...
[把你要拆解的逐字稿放这里]
"""

response = client.chat.completions.create(
    model="deepseek-chat",  # 或 gpt-4o, claude-opus
    messages=[
        {"role": "system", "content": skill},
        {"role": "user", "content": f"请拆解这条逐字稿：\n\n{transcript}"}
    ]
)
print(response.choices[0].message.content)
```

### 验证 checklist

测试 3-5 条不同质量的逐字稿（你已经知道哪条爆、哪条没爆），看 SKILL 是否：

- [ ] 钩子评分跟你的直觉一致（差距 ≤ 2 分）
- [ ] 爆点定位准确（找出来的句子确实是你认为爆的那句）
- [ ] 可复刻清单可操作（不是 "写好钩子" 这种废话）
- [ ] 不会美化低质量样本（如果给一条普通视频，它会如实给低分）
- [ ] 严格 cite 原文（不会臆测）

如果某项不达标，回去改 `SKILL.md` 对应章节，重新测。

## 迭代建议

测出来差距后，**优先迭代以下部分**（按改动收益从高到低）：

1. **`几个对照例子（few-shot）`** — 这是 LLM 最依赖的部分。把你测出来的 3-5 个真实案例（高/中/低分各一个）的拆解结果整理进去，下一轮分析质量会立刻提升一个台阶。
2. **`领域知识：赛道特异性`** — 你做哪个赛道，就把那个赛道的特征模式补充清楚。
3. **`行为约束`** — 如果你发现 LLM 经常犯某个错（比如美化分析），就加一条约束。
4. **维度/评分** — 如果发现某个维度区分度低（高分低分都打这个分），考虑删掉或合并。
