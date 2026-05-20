---
name: dfx-review
version: "2.4.0"
description: 扫描 Java/Spring 电商微服务后端代码仓库，全量读取代码文件，识别 DFX（Design for eXcellence）设计模式。自动发现所有微服务，逐个扫描业务逻辑和 DFX 能力，生成多服务对比 Dashboard HTML 报告。当用户提到"DFX审视""运维审视""DFX扫描""运维检查""生产就绪评估"时使用此 skill。
tags:
  - java
  - spring
  - microservices
  - dfx
  - operational-review
  - backend
author: DFX Team
dependencies:
  - references/analysis-framework.md
  - references/domains.json
  - references/dashboard-template.html
---

# DFX 运维审视 Skill v2

扫描 Java/Spring 微服务群，全量读取代码，从文件内容（而非关键词匹配）推断 DFX 设计模式。
支持多服务并行扫描、跨服务对比、单服务详情。生成 Dashboard HTML 报告。

## 适用场景

用户说"做 DFX 审视""扫描 DFX""生成 DFX 报告""运维设计审视""检查生产就绪度"时触发。
支持 Spring Boot / Spring Cloud 多模块或多仓库微服务项目。

## 前置条件

- 当前工作目录应为 Java/Spring 项目的根目录（或微服务群的父目录）
- 仅使用 Claude Code 内置工具（Glob、Grep、Read、Write、Bash）
- 不需要外部依赖

---

## 阶段零：环境预检

在开始扫描前，先快速验证工作目录是否包含可扫描的 Java 项目。

**预检步骤**：

1. Glob 查找 `**/pom.xml` 和 `**/build.gradle*`
2. 若均未找到：中止扫描，提示"未检测到 Maven 或 Gradle 项目。请确认当前目录为 Java 项目根目录。"
3. 若找到 `pom.xml`：检查是否包含 `<modules>` 节点（多模块）或直接含 Java 源文件（单模块）
4. 若找到 `build.gradle*`：检查是否含 `java` 插件或 `include` 语句
5. 验证 `src/main/java` 目录是否存在，若不存在：中止扫描，提示"未找到 src/main/java，请确认项目结构"

**预检输出**：
```
[预检] 检测到 Maven 单模块项目：order-service
[预检] Spring Boot 版本：3.2.0（从 pom.xml 推断）
[预检] 源文件目录：src/main/java ✓
[预检] 扫描就绪，开始阶段一...
```

---

## 工作流程（6 个阶段：预检 + 5 步扫描）

---

### 阶段一：服务发现

识别当前目录下有哪些微服务。

1. **读取构建文件**：Glob 查找 `pom.xml`、`settings.gradle`。
2. **检测多模块**：
   - 若 `pom.xml` 含 `<modules>`，则每个 module 视为一个候选服务
   - 若 `settings.gradle` 含 `include`，同理
   - 若没有多模块标识，则检查根目录下是否有子目录含独立 `pom.xml` 或 `build.gradle`
3. **验证服务**：对每个候选，确认存在 `src/main/java` 目录和至少一个 Java 文件。若找到 `@SpringBootApplication` 标注的类，确认为 Spring Boot 服务。
4. **单服务退化**：若仅发现一个服务，后续阶段仅扫描该服务，报告仅展示单服务视图。
5. **收集元数据**：对每个服务收集：
   ```
   name（模块名/目录名）、totalJavaFiles、springBootVersion、buildSystem
   ```
   输出形如 `serviceList[]`。

---

### 阶段二：逐服务全量扫描

对 `serviceList` 中每个服务，执行以下子步骤。**从代码文件实际内容分析 DFX，而非 grep 模式匹配。**

---

**阶段二检查点（验证通过后进入下一子步骤）**

| 检查点 | 验证条件 | 若失败 |
|--------|---------|--------|
| 文件清单非空 | Glob 找到 ≥1 个 .java 文件 | 报告"服务无 Java 文件"，跳过该服务 |
| 分批策略合理 | P0 ≤8 个文件，P1 ≤15 个文件 | 调整每批大小，确保内存可控 |
| 关键文件已读 | 至少读过 1 个 Service/Controller/Config | 发出警告，继续扫描但降低置信度 |
| 扫描覆盖率 | 已读文件占总文件数 <30% | 警告"覆盖率不足"，结果置信度降低 |

**扫描置信度评级**：

| 置信度 | 条件 | 影响 |
|--------|------|------|
| **高** | 已读文件 ≥50%，P0 全覆盖，关键类全读 | 最终评分如实呈现 |
| **中** | 已读文件 30-50%，或 P0 未全覆盖 | 最终评分 ×0.9 折扣 |
| **低** | 已读文件 <30%，或仅读 Entity/DTO/VO | 最终评分 ×0.7 折扣，报告中标注"采样不足" |

---

#### 子步骤 2.1：列出文件清单

Glob 找出该服务 `src/main/java` 下所有 `.java` 文件。

**文件优先级分组**：

| 优先级 | 文件类型 | Glob 模式 | 说明 |
|--------|---------|----------|------|
| **P0 必读** | Service/Controller/Config | `**/*Service*.java` `**/*Controller*.java` `**/*Config*.java` `**/*Configuration*.java` | DFX 信号最密集 |
| **P0 必读** | Aspect/Interceptor/Filter/Listener | `**/aspect/**` `**/interceptor/**` `**/filter/**` `**/listener/**` | 切面、拦截、过滤逻辑含大量 DFX |
| **P0 必读** | 配置文件 | `**/application*.yml` `**/application*.properties` `**/bootstrap*.yml` `**/logback*.xml` `**/log4j*.xml` `pom.xml` `build.gradle` | 配置层 DFX |
| **P1 选读** | Repository/Mapper | `**/*Repository*.java` `**/*Mapper*.java` `**/*Dao*.java` | 数据访问的异常/超时/缓存 |
| **P1 选读** | Handler/Processor | `**/*Handler*.java` `**/*Processor*.java` `**/*Consumer*.java` `**/*Producer*.java` | 事件/MQ 处理逻辑 |
| **P2 可跳过** | Entity/DTO/VO/Enum | `**/entity/**` `**/dto/**` `**/vo/**` `**/enums/**` `**/model/**` `**/domain/**` | 纯数据，DFX 信号极少 |
| **P2 可跳过** | Test | `**/*Test*.java` `**/*Tests*.java` | 测试代码不纳入 |

#### 子步骤 2.2：分批读取与分析

按优先级从高到低分批 Read。每批 5-8 个文件。读取时逐文件分析，**从文件实际内容中提取 DFX 信号**。

分析时参考 `references/analysis-framework.md` 中列出的代码信号清单。**从文件实际内容中提取以下 Spring/Java 模式**：

**每读一个文件，按以下清单逐项检查**（每项检查的是文件内容中是否存在对应模式，而非简单的关键词匹配）：

| # | 检查项 | 找什么（Spring/Java 模式） | 对应维度 |
|---|--------|--------------------------|---------|
| 1 | **日志框架** | `@Slf4j`、`Logger` 声明、`log.info/error/warn/debug` 调用 | 2.1 日志诊断 |
| 2 | **日志上下文** | `MDC.put("traceId"`、`MDC.put("orderId"`、`JSONEncoder` / `LogstashEncoder` | 2.1 日志诊断 |
| 3 | **全局异常处理** | `@RestControllerAdvice`、`@ExceptionHandler`、`BusinessException` 基类 | 2.2 异常处理 |
| 4 | **统一错误响应** | `ErrorResponse`、`ApiError` DTO 定义（含 code/message/status 字段）| 2.2 异常处理 |
| 5 | **指标埋点** | `@Timed`、`Counter.builder`、`Timer.builder`、`MeterBinder` 实现 | 2.3 指标监控 |
| 6 | **健康检查** | `HealthIndicator`、`AbstractHealthIndicator` 实现、`livenessState/readinessState` 配置 | 2.4 健康检查 |
| 7 | **熔断降级** | `@CircuitBreaker(` + `fallbackMethod`（成对出现）、`@Bulkhead(`、`@TimeLimiter(` | 2.5 熔断与韧性 |
| 8 | **重试** | `@Retryable(`、`@Recover`、指数退避配置（`multiplier > 1`）| 2.7 重试 |
| 9 | **缓存** | `@Cacheable(` + `@CacheEvict(` 成对、`CacheManager` 配置、TTL 设置 | 2.6 缓存 |
| 10 | **异步执行** | `@Async(`、`ThreadPoolTaskExecutor` Bean（`setCorePoolSize` 等配置）、`RejectedExecutionHandler` | 2.9 异步线程池 |
| 11 | **链路追踪** | `io.opentelemetry` 导入、`@WithSpan(` / `@NewSpan(` 注解、`brave.Tracer` 编程式追踪 | 2.8 链路追踪 |
| 12 | **配置属性** | `@ConfigurationProperties(` + `@Validated`、特性开关 `@ConditionalOnProperty(` | 2.10 配置管理 |
| 13 | **API 版本化** | URL 含 `/v[0-9]+/` 或 `X-API-Version` 头、Controller 上有 `@Deprecated` | 2.11 API 版本化 |
| 14 | **优雅关闭** | `server.shutdown=graceful` + `timeout-per-shutdown-phase`、`@PreDestroy` 清理钩子 | 2.12 优雅关闭 |
| 15 | **安全防护** | `RateLimiter` 过滤器、`CorsConfigurationSource` 具体域名配置、`MODE_INHERITABLETHREADLOCAL` | 2.13 安全 DFX |
| 16 | **订单幂等** | `X-Idempotency-Key` / `requestId` 参数、`SETNX` 原子检查、TTL 清理 `@Scheduled` | 3.1 订单幂等 |
| 17 | **库存锁** | `SELECT FOR UPDATE` SQL、`@Lock(` 注解、`Redisson` / `RedisLock` 分布式锁实现 | 3.2 库存锁定 |
| 18 | **支付状态机** | 支付状态枚举（UNPAID/PAYING/PAID/REFUNDED/FAILED）、`outTradeNo` 幂等、`verifySign` | 3.3 支付事务 |
| 19 | **分布式事务** | `@GlobalTransactional`（Seata）、`Outbox` 表 + `@TransactionalEventListener`、`@Saga` 编排 | 3.4 分布式事务 |
| 20 | **秒杀防护** | Redis 库存预加载（`SETNX` 库存键）、MQ 队列（`@KafkaListener` 消费）、用户级 `@RateLimiter(` | 3.5 秒杀防护 |
| 21 | **状态机** | `StateMachine` 接口实现、`squirrel-foundation` / `stateless4j` 依赖、`@Scheduled` 卡单检测 | 3.6 状态机监控 |
| 22 | **第三方降级** | `interface.*Client` / `interface.*Gateway` 接口声明 + 多实现、每服务独立 `@CircuitBreaker` | 3.7 第三方降级 |
| 23 | **业务告警** | `Counter.builder("order.created")` 业务指标、告警阈值配置（`alert.threshold`）| 3.8 业务告警 |
| 24 | **漏斗追踪** | `AnalyticsEvent` / `FunnelEvent` 类名、漏斗转化 `Counter`（如 `checkout_to_payment`）| 3.9 漏斗追踪 |
| 25 | **超时管理** | `@Transactional(timeout=N)` 按操作区分超时、`RestTemplate`/`WebClient` 超时配置 | 3.10 超时管理 |
| 26 | **数据对账** | `@Scheduled` 对账任务、类名含 `reconcil`/`settlement`、`CHECK` 约束防超卖 | 3.11 数据一致性 |

记录时格式：
```
文件: XxxService.java
信号: [日志] @Slf4j + log.info/error 混用
     [异常] try/catch 包裹外部调用，但未抛业务异常
     [熔断] 未发现 CircuitBreaker
     [指标] 未发现 @Timed 或 Counter
     ...
```

#### 子步骤 2.3：聚合维度评分

每个文件读完后，将信号聚合到 24 个维度（13 通用 + 11 业务）。

**判定标准**：

| 状态 | 标准 |
|------|------|
| **已具备** | 在 3+ 个关键文件（Service/Controller/Config）中发现该维度信号，配置完整，配套齐全 |
| **部分具备** | 仅在 1-2 个文件中发现，或配置不完整，或缺少配套（如熔断无降级、缓存无淘汰） |
| **缺失** | 所有已读文件中均未发现该维度信号 |

维度细节和信号清单见 `references/analysis-framework.md`。

#### 子步骤 2.4：业务领域发现

从已读取的文件中提取业务领域。基于包名关键词、类名关键词（`Order`、`Payment`、`Inventory` 等），使用 `references/domains.json` 中的 `vocabulary` 映射为中文标签。

---

### 阶段三：跨服务汇总

所有服务扫描完成后，生成跨服务对比：

1. **服务排名**：按综合 DFX 得分降序排列
2. **共性缺口**：统计每个维度在多少服务中标记为"缺失"或"部分具备"。取缺失率最高的 Top 5 作为"跨服务共性短板"
3. **各服务得分矩阵**：每个服务 × 每个维度的得分矩阵，用于跨服务雷达图
4. **服务成熟度分级**：按综合得分将服务分为四级
   - 🏆 优秀（≥0.80）：通用和业务 DFX 均达标
   - ✅ 良好（0.60-0.79）：通用 DFX 无高风险缺口
   - ⚠️ 一般（0.40-0.59）：存在中高风险缺口
   - 🔴 薄弱（<0.40）：存在高风险维度（3.1/3.2/3.3/3.4/3.5）

---

### 阶段四：评分计算

每服务独立评分：

```
通用DFX得分 = 该服务 13 个通用维度得分之和 / 13
业务DFX得分 = 该服务 11 个业务维度得分之和 / 11
服务综合得分 = 通用DFX × 0.50 + 业务DFX × 0.50
```

**按置信度折扣**：
- 高置信度：评分不折扣
- 中置信度：评分 × 0.9
- 低置信度：评分 × 0.7，报告中标注 ⚠️采样不足

跨服务整体评分取各服务得分的算术平均。

得分评级（0.00-1.00）：
- 0.80+ 优秀、0.60+ 良好、0.40+ 一般、0.20+ 薄弱、0.00-0.19 严重不足

---

### 阶段五：生成多服务报告

1. **构建 JSON 数据结构**：

```json
{
  "scanTimestamp": "2026-05-18 15:30:00",
  "scanDuration": "45s",
  "totalServices": 3,
  "services": [
    {
      "name": "order-service",
      "totalJavaFiles": 120,
      "springBootVersion": "3.2.0",
      "buildSystem": "Maven",
      "businessDomains": [
        { "name": "订单处理", "detected": true, "fileCount": 28, "keyClasses": ["..."] }
      ],
      "genericDFX": [
        { "id": "2.1", "name": "日志诊断", "status": "present", "score": 1.0,
          "summary": "...", "evidence": [{"file":"","snippet":""}], "recommendations": [] }
      ],
      "businessDFX": [ /* 同结构 */ ],
      "scores": { "overall": 0.72, "genericDFX": 0.68, "businessDFX": 0.76, "confidence": "high" },
      "remediation": [
        { "priority": "P0", "phase": "快速见效", "dimensionId": "2.12", "dimensionName": "优雅关闭",
          "action": "...", "targetFiles": ["..."], "codePattern": "...", "effort": "2min", "impact": "..." }
      ]
    }
  ],
  "crossService": {
    "ranking": ["order-service", "payment-service"],
    "comparisonMatrix": {
      "order-service": { "overall": 0.72, "genericDFX": { "2.1": 1.0, "2.2": 0.5, ... }, "businessDFX": { "3.1": 0.5, ... } },
      "payment-service": { ... }
    },
    "commonGaps": [
      { "dimensionId": "2.8", "dimensionName": "链路追踪", "affectedCount": 3, "totalServices": 3 }
    ]
  }
}
```

2. **读取** `references/dashboard-template.html`。

3. **替换**模板中的 `__REPORT_DATA__` 为 JSON 字符串（注意转义）。

4. **写入** `dfx-report.html` 到当前工作目录。

5. **报告**：`DFX 审视完成。共扫描 N 个微服务，报告已保存至 dfx-report.html。`

---

## 边界情况处理

| 场景 | 处理 |
|------|------|
| 单服务项目 | 退化为单服务报告视图，隐藏跨服务对比区 |
| Java 文件 > 2000/服务 | 对 Entity/DTO/VO/Enum/Test 彻底跳过，仅读 P0+P1 |
| 非 Maven/Gradle | 使用目录名作为服务名，跳过依赖版本检测 |
| 非 Spring 项目 | 标注"非 Spring 项目"，DFX 评分仅基于 Java 通用实践 |
| 无 Java 文件 | 中止："未找到 Java 源文件。" |
| 模板文件找不到 | 在 SKILL.md 所在目录下搜索 references/ 路径 |
| Gradle 项目无构建文件 | 尝试 `gradlew` 或 `build.gradle.kts`，检测 Kotlin DSL |
| 多仓库微服务 | 支持 glob 模式如 `../*/pom.xml` 扫描同级目录 |
| 服务名冲突 | 使用 `groupId:artifactId` 作为唯一标识 |
| 文件编码问题 | UTF-8 优先，失败则尝试 GBK，仍失败则跳过并记录 |

## 参考资料

- `references/analysis-framework.md` — DFX 维度定义、代码信号清单、分类标准、改造指引
- `references/domains.json` — 业务领域词汇映射表 + 过滤路径配置
- `references/dashboard-template.html` — 自包含多服务仪表盘 HTML 模板
