---
name: dfx-review
description: 扫描 Java/Spring 电商后端代码，识别 DFX（Design for eXcellence）设计模式。
  梳理业务逻辑，检查通用 DFX 能力（日志、指标、熔断、健康检查、缓存、链路追踪等）和
  业务 DFX 能力（幂等、库存锁、Saga、秒杀防护等）。生成自包含的仪表盘 HTML 报告。
  当用户提到"DFX审视""运维审视""DFX扫描""运维检查""生产就绪评估"时使用此 skill。
---

# DFX 运维审视 Skill

扫描 Java/Spring 电商代码仓库，梳理业务逻辑，识别通用和业务 DFX 设计模式，
生成 Dashboard 风格的可视化 HTML 报告。

## 适用场景

用户说"做 DFX 审视""扫描 DFX""生成 DFX 报告""运维设计审视""检查生产就绪度"时触发。
适用于 Spring Boot / Spring Cloud 项目。

## 前置条件

- 当前工作目录应为 Java/Spring 项目根目录
- 仅使用 Claude Code 内置工具（Glob、Grep、Read、Write），无需安装额外依赖

## 工作流程

按顺序执行以下七个阶段。每个阶段开始时向用户报告进度。

---

### 阶段一：项目发现

1. Glob 查找构建文件：`pom.xml`、`build.gradle`、`build.gradle.kts`
2. 如果找到，读取构建文件并提取：
   - 从 `<artifactId>` 或 `rootProject.name` 获取项目名
   - 从 `<parent>` 或依赖版本获取 Spring Boot 版本
   - 如有 `spring-cloud-dependencies` BOM，获取 Spring Cloud 版本
3. 如果没有构建文件：使用当前目录名作为项目名，标注"构建系统未知"
4. Glob 查找 `**/*.java` 统计 Java 源文件总数
5. Grep 查找 `@SpringBootApplication` 定位主应用类
6. Bash：`find src/main/java -type d | head -30` 列出包结构

收集以下元数据字段：
```
projectName（项目名）、totalJavaFiles（文件总数）、buildSystem（Maven/Gradle/Unknown）、
springBootVersion、springCloudVersion、mainClass（主类）、packageRoots（包路径列表）
```

---

### 阶段二：业务领域检测

对以下 12 个电商业务领域，分别 Grep 类名模式（`--include="*.java"`，排除 `target/` 和 `build/` 目录）：

| 业务领域 | Grep 模式 |
|---------|----------|
| 订单处理 | `class.*Order` |
| 支付/账单 | `class.*Payment\|class.*Transaction\|class.*Refund` |
| 库存管理 | `class.*Inventor\|class.*Stock\|class.*Sku\|class.*Warehouse` |
| 购物车/结算 | `class.*Cart\|class.*Checkout\|class.*Basket` |
| 用户/账户 | `class.*User\|class.*Account\|class.*Customer\|class.*Auth` |
| 商品/目录 | `class.*Product\|class.*Catalog\|class.*Category` |
| 促销/优惠券 | `class.*Coupon\|class.*Promotion\|class.*Discount` |
| 物流/配送 | `class.*Shipping\|class.*Logistics\|class.*Delivery\|class.*Fulfill` |
| 消息通知 | `class.*Notification\|class.*Notif\|class.*Email.*Service\|class.*Sms` |
| 秒杀/抢购 | `class.*Flash\|class.*Seckill\|class.*Spike\|class.*Burst` |
| 评价/评分 | `class.*Review\|class.*Rating\|class.*Feedback` |
| 管理后台 | `class.*Admin\|class.*Dashboard\|class.*Ops` |

对每个领域：
- 统计匹配文件数；提取最多 5 个类名
- 若 fileCount > 0 标记 `detected: true`，否则 `detected: false`
- 对检测到的领域，记录 3-5 个关键类名

---

### 阶段三：通用 DFX 扫描（13 个维度）

对以下每个维度执行指定的 Grep 命令。参照 `references/analysis-framework.md` 中的标准，
将发现分类为"已具备"/"部分具备"/"缺失"。每个维度收集最多 5 条证据，
包含文件路径和代码片段。

**2.1 日志与诊断**
- Grep: `LoggerFactory\.getLogger|@Slf4j` — SLF4J 使用情况
- Grep: `MDC\.put\(|MDC\.clear\(` — 上下文日志（traceId/orderId）
- Grep: `logback-spring\.xml|logstash` — JSON 编码器配置
- Grep: `@ToString\.Exclude|@JsonIgnore.*password|@JsonIgnore.*phone` — 敏感数据脱敏

**2.2 异常处理**
- Grep: `@ControllerAdvice|@RestControllerAdvice` — 全局异常处理器
- Grep: `@ExceptionHandler\(` — 异常处理方法
- Grep: `extends RuntimeException` — 业务异常体系
- Grep: `ErrorResponse|ApiError|ErrorResult` — 统一错误响应结构

**2.3 指标监控**
- Grep: `import io\.micrometer` — Micrometer 依赖
- Grep: `@Timed\(` — 方法级耗时打点
- Grep: `Counter\.builder\(|meterRegistry\.counter\(` — 自定义业务计数器
- Grep: `MeterBinder` — 自定义指标注册

**2.4 健康检查**
- Grep: `HealthIndicator` — 自定义健康指示器
- Grep: `livenessState|readinessState` — K8s 探针支持
- Grep: `management\.endpoint\.health` — 健康端点配置

**2.5 熔断与韧性**
- Grep: `@CircuitBreaker\(|@Bulkhead\(|@RateLimiter\(|@TimeLimiter\(` — Resilience4j 注解
- Grep: `fallbackMethod` — 降级方法
- Grep: `import io\.github\.resilience4j|import com\.alibaba\.csp\.sentinel` — 韧性库依赖

**2.6 缓存**
- Grep: `@Cacheable\(|@CacheEvict\(|@CachePut\(` — 缓存注解
- Grep: `@EnableCaching` — 缓存开关
- Grep: `CacheManager|RedisCacheManager` — 缓存配置
- Grep: `spring\.cache` — 缓存 TTL 配置

**2.7 重试**
- Grep: `@Retryable\(` — 重试注解
- Grep: `@Recover` — 恢复方法
- Grep: `import org\.springframework\.retry` — Spring Retry 依赖

**2.8 链路追踪**
- Grep: `import io\.opentelemetry|brave\.Tracer|spring-cloud-starter-sleuth` — 追踪 SDK
- Grep: `@WithSpan\(|@SpanTag\(|@NewSpan\(` — Span 注解
- Grep: `tracer\.nextSpan|tracer\.currentSpan` — 编程式 Span

**2.9 线程池与异步**
- Grep: `@Async\(` — 异步方法
- Grep: `ThreadPoolTaskExecutor` — 自定义线程池
- Grep: `RejectedExecutionHandler|setRejectedExecutionHandler` — 拒绝策略

**2.10 配置管理**
- Grep: `@ConfigurationProperties\(` — 类型化配置
- Grep: `@RefreshScope` — 动态刷新
- Grep: `@Validated.*ConfigurationProperties|ConfigurationProperties.*@Validated` — 配置校验
- Grep: `@ConditionalOnProperty\(` — 特性开关

**2.11 API 版本化**
- Grep: `/v[0-9]+/` — URL 路径版本
- Grep: `@Deprecated` — 废弃 API 标记
- Grep: `@JsonIgnoreProperties\(ignoreUnknown\s*=\s*true\)` — 向下兼容

**2.12 优雅关闭**
- Grep: `server\.shutdown\s*[=:]\s*graceful` — 优雅关闭配置
- Grep: `@PreDestroy` — 清理钩子

**2.13 安全 DFX**
- Grep: `RateLimiter|RateLimit.*Filter|rate.*limit` — 接口限流
- Grep: `MODE_INHERITABLETHREADLOCAL|DelegatingSecurityContext` — 认证上下文传递
- Grep: `CorsConfigurationSource|@CrossOrigin` — CORS 配置

对每个搜索返回结果：记录文件路径、出现次数、判断应用一致性。

---

### 阶段四：业务 DFX 扫描（11 个维度）

**3.1 订单幂等性**
- Grep: `[Ii]dempoten` — 幂等概念
- Grep: `X-Idempotency-Key|idempotencyKey|requestId` — 客户端幂等键
- Grep: `SETNX|setIfAbsent|unique.*constraint|DuplicateKeyException` — 原子存储

**3.2 库存锁定与释放**
- Grep: `SELECT.*FOR UPDATE|@Lock\(|PESSIMISTIC` — 悲观锁
- Grep: `Redisson|RedisLock|distributedLock|tryLock` — 分布式锁
- Grep: `releaseStock|releaseInventory|unlockStock|compensateStock` — 库存释放

**3.3 支付事务模式**
- Grep: `outTradeNo|transactionId.*unique|paymentKey` — 支付幂等
- Grep: `verifySign|checkSign|validateNotify|verifySignature` — 回调验签
- Grep: `reconcil|settlement` — 对账逻辑

**3.4 分布式事务**
- Grep: `@GlobalTransactional|io\.seata` — Seata 分布式事务
- Grep: `@Saga|SagaOrchestrat|saga` — Saga 模式
- Grep: `@Compensable|@Compensate|compensateMethod` — 补偿处理
- Grep: `Outbox|outbox|@TransactionalEventListener` — Outbox 模式

**3.5 秒杀/高并发防护**
- Grep: `pre.*load.*stock|preload.*inventory|redis.*stock.*flash` — Redis 预加载
- Grep: `queue.*order|send.*queue.*order|producer.*order|consumer.*order` — MQ 排队
- Grep: `rate.*limit.*user|perUser.*rate|user.*rate.*limit` — 用户级限流

**3.6 状态机监控**
- Grep: `StateMachine|squirrel-foundation|stateless4j|state.*transition` — 状态机库
- Grep: `@Scheduled.*status|stuck.*order|prolonged.*state` — 卡单检测
- Grep: `status.*Counter|state.*change.*metric|transition.*counter` — 状态转换指标

**3.7 第三方服务降级**
- Grep: `interface.*Client|interface.*Gateway|interface.*Provider` — 外部服务抽象
- Grep: `@CircuitBreaker.*name` — 与外部服务名映射，确认每个外部服务有独立熔断
- Grep: `fallback.*cached|fallback.*degrad|fallback.*alternative` — 降级逻辑

**3.8 业务告警指标**
- Grep: `Counter\.builder.*order|Counter\.builder.*payment|Counter\.builder.*business` — 业务计数器
- Grep: `alert.*threshold|alert.*rate|SLA|SLI` — 告警配置

**3.9 用户旅程/漏斗追踪**
- Grep: `AnalyticsEvent|FunnelEvent|UserActionEvent|TrackingEvent` — 分析事件
- Grep: `viewed.*event|added.*cart.*event|checkout.*event|placed.*order.*event` — 漏斗事件

**3.10 超时管理**
- Grep: `@Transactional\(timeout|setReadTimeout|setConnectTimeout|responseTimeout` — 超时配置
- Grep: `@TimeLimiter\(` — Resilience4j 时间限制器

**3.11 数据一致性对账**
- Grep: `@Scheduled.*reconcil|@Scheduled.*settlement|@Scheduled.*consistency` — 定时对账
- Grep: `reconcil|consistency.*check|compare.*gateway|compare.*remote` — 对账逻辑

---

### 阶段五：分类评定

对每个维度，分类为"已具备""部分具备"或"缺失"：

**已具备（评分 1.0）**：
- 模式在 3 处以上出现，或出现在专门的配置类中
- 跨模块一致应用
- 配置或集成可见（配置类、yml 条目）
- 配套机制齐全（如熔断有降级，缓存有淘汰）

**部分具备（评分 0.5）**：
- 模式仅在 1-2 处出现，或跨模块不一致
- 有注解但缺配置
- 有模式但缺配套（如重试缺恢复，熔断缺降级）
- 有依赖但无自定义配置

**缺失（评分 0.0）**：
- 未找到相关 import、注解或配置

每个维度记录：
- `status`: "present" | "partial" | "missing"
- `score`: 1.0 | 0.5 | 0.0
- `evidence`: `{file, snippet}` 数组（最多 5 条）
- `summary`: 一句话总结
- `recommendations`: 改进建议数组（针对 partial/missing）

---

### 阶段六：评分计算

```
通用DFX得分 = 通用DFX各维度得分之和 / 13
业务DFX得分 = 业务DFX各维度得分之和 / 11
领域覆盖度 = 检测到的业务领域数 / 12
综合得分 = 通用DFX × 0.40 + 业务DFX × 0.40 + 领域覆盖度 × 0.20
```

得分评级：
- 0.80 - 1.00：优秀
- 0.60 - 0.79：良好
- 0.40 - 0.59：一般
- 0.20 - 0.39：薄弱
- 0.00 - 0.19：严重不足

---

### 阶段七：生成 HTML 报告

1. **构建 JSON 数据结构**，参照以下 schema：

```json
{
  "projectName": "项目名",
  "scanTimestamp": "扫描时间（ISO 格式）",
  "scanDuration": "扫描耗时",
  "totalJavaFiles": 0,
  "buildSystem": "Maven|Gradle|Unknown",
  "springBootVersion": "版本号",
  "springCloudVersion": "版本号或 null",
  "businessDomains": [
    { "name": "领域名", "detected": true, "fileCount": 0, "keyClasses": [] }
  ],
  "genericDFX": [
    { "id": "2.1", "name": "维度名", "status": "present|partial|missing",
      "score": 1.0, "summary": "一句话评估", "evidence": [{"file":"文件路径","snippet":"代码片段"}],
      "recommendations": ["改进建议"] }
  ],
  "businessDFX": [
    { "id": "3.1", "name": "维度名", "status": "present|partial|missing",
      "score": 1.0, "summary": "一句话评估", "evidence": [{"file":"文件路径","snippet":"代码片段"}],
      "recommendations": ["改进建议"] }
  ],
  "scores": {
    "overall": 0.0, "genericDFX": 0.0, "businessDFX": 0.0, "landscapeCoverage": 0.0
  }
}
```

2. **读取** skill 目录下的 `references/dashboard-template.html`。

3. **替换**模板中的 `__REPORT_DATA__` 占位符为 JSON 字符串。
   JSON 转义注意事项：
   - 文件路径中的反斜杠需转义（`\` → `\\`）
   - 字符串内的双引号需转义（`"` → `\"`）
   - 代码片段中的换行符需要移除或转义
   - 确保 JSON 有效 — 无尾随逗号、括号匹配

4. **写入** 当前工作目录下的 `dfx-report.html`。

5. **报告** 完成：`DFX 审视完成。报告已保存至 {cwd}/dfx-report.html。综合得分：{score}分 — {评级}。`

---

## 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| 无 Java 文件 | 中止："未找到 Java 源文件。请在 Java 项目根目录运行此 skill。" |
| 无构建文件 | 使用目录名作为项目名，标注"构建系统未知" |
| 多模块 Maven/Gradle | 找到包含 `@SpringBootApplication` 的模块，仅扫描该模块 |
| 非 Spring 项目 | 对适用维度执行通用 Java 分析；标注"非 Spring 项目" |
| 检测到的业务领域 < 3 | 仍生成完整报告；标注"电商领域覆盖偏少" |
| Java 文件 > 5000 | 仅扫描 `service/`、`controller/`、`config/` 子目录 |
| Grep 无输出 | 该维度评分"缺失"；证据标注"未找到匹配模式" |
| 排除生成代码 | 所有 grep 添加 `--glob='!target/**'` 和 `--glob='!build/**'` |
| 模板文件找不到 | 在 SKILL.md 所在目录下搜索，推导 references/ 路径 |

## 参考资料

- `references/analysis-framework.md` — 详细的搜索模式、分类标准和各维度风险等级
- `references/dashboard-template.html` — 自包含 HTML 仪表盘模板（SVG 图表 + 内联 CSS/JS）
