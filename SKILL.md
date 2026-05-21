---
name: dfx-review
version: "2.9.0"
description: 扫描 Java/Spring 电商微服务后端，识别 DFX（Design for eXcellence）设计模式。自动生成跨服务对比 Dashboard。当用户提到"DFX审视""运维扫描""生产就绪评估"时使用。
tags: [java, spring, microservices, dfx, operational-review]
dependencies:
  - references/analysis-framework.md
  - references/scanning_strategy.md
  - references/report_schema.md
  - references/domains.json
  - references/dashboard-template.html
---

# DFX 运维审视 Skill

从代码文件内容推断 DFX 设计模式（日志、异常、熔断、幂等、事务等），生成可视化多服务 Dashboard。

## 触发词
- "DFX 审视"、"运维设计检查"、"生产就绪度评估"、"扫描 DFX"

## 核心工作流 (6 阶段)

### Phase 0: 环境预检
验证 Maven/Gradle 项目结构及 `src/main/java`。详见 `references/scanning_strategy.md`。

### Phase 1: 服务发现
识别多模块或单模块项目中的微服务边界，收集元数据（SpringBoot 版本、文件数等）。

### Phase 2: 逐服务全量扫描 (关键)
1. **清单分组**：按 P0/P1/P2 优先级分批读取文件。参考 `references/scanning_strategy.md`。
2. **模式识别**：**必须阅读 `references/analysis-framework.md`** 获取 26 项 DFX 判定标准。
3. **信号记录**：从代码实际内容（注解、API 调用、配置）中提取信号，严禁关键词盲匹。

### Phase 3: 跨服务汇总
统计各服务排名、共性短板、成熟度分级（优秀/良好/一般/薄弱）。

### Phase 4: 评分计算
计算通用 DFX (13 维度) 与业务 DFX (11 维度) 得分。根据已读文件覆盖率应用**置信度折扣**。

### Phase 5: 生成报告
组装 JSON 数据模型（参考 `references/report_schema.md`），填充 `references/dashboard-template.html` 并输出为 `dfx-report.html`。

## 资源导航

- **DFX 判定标准大全**：`references/analysis-framework.md` (包含 26 个维度的代码信号清单)。
- **扫描策略与置信度**：`references/scanning_strategy.md` (优先级分组、检查点、边界处理)。
- **报告 JSON 结构**：`references/report_schema.md` (用于 HTML 组装的数据协议)。
- **业务领域词汇表**：`references/domains.json`。

## 执行约束

1. **内容驱动**：从文件实际内容推断模式，不依赖文件名。
2. **分批执行**：每批控制在 5-8 个文件，防止上下文溢出。
3. **置信度标注**：若读取文件不足 30%，必须在报告中标注“采样不足”。
4. **业务侧重**：重点审视 3.1-3.5 核心业务 DFX（幂等、锁、事务等）。

---
**提示**：在开始分析前，请务必预览 `references/analysis-framework.md` 以确保判定逻辑与项目标准一致。
