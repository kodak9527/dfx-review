---
name: dfx-review
version: "3.0.0"
description: 扫描 Java/Spring 微服务后端，识别 DFX 设计模式并生成 Dashboard。针对内部大模型优化，采用确定性 Python 脚本计算得分。
tags: [java, spring, microservices, dfx, operational-review]
dependencies:
  - references/analysis-framework.md
  - references/scanning_strategy.md
  - references/domains.json
  - references/dashboard-template.html
  - scripts/dfx_parser.py
---

# DFX 运维审视 Skill

从代码内容推断 DFX 模式。采用“LLM 提取证据 + Python 脚本打分”的健壮架构，适配各种推理能力的模型。

## 触发词
- "DFX 审视"、"运维设计检查"、"扫描 DFX"

## 核心工作流 (3 阶段)

### Phase 1: 扫描与证据提取 (LLM 执行)
1. **环境预检**：验证项目结构（见 `references/scanning_strategy.md`）。
2. **证据抽取**：
   - 按照优先级分组读取代码文件。
   - **严格查阅 `references/analysis-framework.md`** 中的 26 个维度判定准则。
   - 为每个服务生成一个 Markdown 报告，必须包含“证据提取”和“状态判定”。
   - 将报告保存为 `output/dfx_raw_<service_name>.md`。

### Phase 2: 结构化解析与打分 (确定性脚本)
运行 Python 脚本处理 LLM 生成的原始报告。脚本会自动提取判定结论，并根据预设权重计算得分。
```bash
# 确保已安装 python
python scripts/dfx_parser.py --dir output/ --template references/dashboard-template.html --output dfx-report.html
```

### Phase 3: 结果交付
告知用户 DFX 审视已完成，并提供 `dfx-report.html` 的位置。

## 资源导航

- **阅卷指南**：`references/analysis-framework.md` (包含正/反例及思维链要求)。
- **扫描策略**：`references/scanning_strategy.md` (文件优先级与采样规则)。
- **解析引擎**：`scripts/dfx_parser.py` (核心算分逻辑)。

## 执行约束 (必须遵守)

1. **思维链强制**：大模型输出分析时，必须包含“意图匹配”和“证据提取”过程。
2. **严禁生成 JSON**：不要让大模型生成任何 JSON 数据，全部使用 Markdown 文本。
3. **严禁脑内算分**：大模型只需给出 `Present/Partial/Missing` 的定性结论，不涉及任何数值计算。
4. **采样置信度**：若代码量巨大导致采样不足，应在分析中诚实记录。

---
**提示**：本 Skill 专为推理能力受限的环境优化，通过脚本托底保证 HTML 报告 100% 可用。
