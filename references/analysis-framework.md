# DFX 分析框架

## 一、业务逻辑提取

从类名模式、包结构、Spring 注解中识别电商业务领域。

| # | 业务领域 | 搜索模式 | 检测标准 |
|---|---------|---------|---------|
| 1 | 订单处理 | `class.*Order` | ≥3 个 Order 相关类 |
| 2 | 支付/账单 | `class.*Payment\|class.*Transaction\|class.*Refund` | ≥2 个支付相关类或支付网关集成 |
| 3 | 库存管理 | `class.*Inventor\|class.*Stock\|class.*Sku\|class.*Warehouse` | ≥2 个库存相关类 |
| 4 | 购物车/结算 | `class.*Cart\|class.*Checkout\|class.*Basket` | ≥1 个购物车或结算类 |
| 5 | 用户/账户 | `class.*User\|class.*Account\|class.*Customer\|class.*Auth` | ≥3 个用户相关类 |
| 6 | 商品/目录 | `class.*Product\|class.*Catalog\|class.*Category` | ≥3 个商品相关类 |
| 7 | 促销/优惠券 | `class.*Coupon\|class.*Promotion\|class.*Discount` | ≥1 个促销或优惠券类 |
| 8 | 物流/配送 | `class.*Shipping\|class.*Logistics\|class.*Delivery\|class.*Fulfill` | ≥1 个物流相关类 |
| 9 | 消息通知 | `class.*Notification\|class.*Notif\|class.*Email.*Service\|class.*Sms` | ≥1 个通知类 |
| 10 | 秒杀/抢购 | `class.*Flash\|class.*Seckill\|class.*Spike\|class.*Burst` | ≥1 个秒杀相关类 |
| 11 | 评价/评分 | `class.*Review\|class.*Rating\|class.*Feedback` | ≥1 个评价类 |
| 12 | 管理后台 | `class.*Admin\|class.*Dashboard\|class.*Ops` | ≥1 个管理后台类 |

**输出**：`{领域名 → 文件数, 关键类名[]}`。文件数 > 0 的领域标记为"已检测到"。

---

## 二、通用 DFX 能力（13 维度）

### 2.1 日志与诊断

| 搜索模式 | 检查内容 |
|---------|---------|
| `LoggerFactory\.getLogger` 或 `@Slf4j` | SLF4J 在 Service 类中的使用 |
| `MDC\.put\(` 或 `MDC\.clear\(` | 上下文日志（traceId/orderId）|
| `logback-spring\.xml` 或 `logstash` | 结构化/JSON 日志配置 |
| `@ToString\.Exclude` 或 `@JsonIgnore`（password, phone 等字段）| 日志敏感数据脱敏 |

- **已具备**：>50% 的 Service 使用 SLF4J/Lombok，MDC 已配置，JSON 编码器，敏感字段已排除
- **部分具备**：使用了 SLF4J 但无 MDC，或无 JSON 日志，或使用不一致
- **缺失**：未找到 SLF4J 导入；使用 System.out

### 2.2 异常处理

| 搜索模式 | 检查内容 |
|---------|---------|
| `@ControllerAdvice` 或 `@RestControllerAdvice` | 全局异常处理器 |
| `@ExceptionHandler\(` | 异常到响应的映射 |
| 异常包下的 `extends RuntimeException` | 业务异常体系 |
| `ErrorResponse` 或 `ApiError` 或 `ErrorResult` | 统一错误响应结构 |

- **已具备**：全局 `@RestControllerAdvice`，分级异常体系，统一错误响应 DTO
- **部分具备**：有处理器但异常结构扁平或错误格式不一致
- **缺失**：无全局异常处理器；直接暴露堆栈信息

### 2.3 指标监控

| 搜索模式 | 检查内容 |
|---------|---------|
| `import io\.micrometer` | Micrometer 依赖 |
| `@Timed\(` | 方法级耗时打点 |
| `Counter\.builder\(` 或 `meterRegistry\.counter\(` | 自定义业务计数器 |
| `MeterBinder` | 自定义指标注册 Bean |

- **已具备**：核心 Service 有 `@Timed`，自定义计数器，MeterBinder Bean
- **部分具备**：有 Micrometer 但仅自动配置的 JVM 指标
- **缺失**：无 Micrometer 导入；无指标埋点

### 2.4 健康检查

| 搜索模式 | 检查内容 |
|---------|---------|
| `HealthIndicator` 或 `AbstractHealthIndicator` | 自定义健康指示器 |
| `livenessState` 或 `readinessState` | K8s 探针支持 |
| yml/properties 中的 `management\.endpoint\.health` | 健康端点配置 |

- **已具备**：为 DB/Redis/MQ 提供了自定义 HealthIndicator，配置了存活/就绪探针
- **部分具备**：仅有自动配置的健康检查；无探针区分
- **缺失**：无 Actuator 或未暴露健康端点

### 2.5 熔断与韧性

| 搜索模式 | 检查内容 |
|---------|---------|
| `@CircuitBreaker\(` | Resilience4j 熔断 |
| `@Bulkhead\(` | 舱壁隔离 |
| `@RateLimiter\(` | 限流 |
| `@TimeLimiter\(` | 超时控制 |
| `fallbackMethod` | 降级方法 |
| `import io\.github\.resilience4j` | Resilience4j 依赖 |
| `import com\.alibaba\.csp\.sentinel` | Sentinel（替代方案）|

- **已具备**：所有远程调用有 `@CircuitBreaker`，池化服务有 `@Bulkhead`，定义了 `fallbackMethod`
- **部分具备**：仅使用了 `@Retry`，或熔断无降级，或只使用默认配置
- **缺失**：无韧性注解或依赖

### 2.6 缓存

| 搜索模式 | 检查内容 |
|---------|---------|
| `@Cacheable\(` | 读穿透缓存 |
| `@CacheEvict\(` | 缓存淘汰 |
| `@CachePut\(` | 写穿透缓存 |
| `@EnableCaching` | 缓存开关 |
| `CacheManager` 或 `RedisCacheManager` | 缓存提供者配置 |
| yml/properties 中的 `spring\.cache\.type` 或 `spring\.cache\.redis\.time-to-live` | 缓存 TTL 配置 |

- **已具备**：CRUD 上有 `@Cacheable` + `@CacheEvict`，分区 TTL，热点缓存有 `sync=true`
- **部分具备**：有 `@Cacheable` 但无淘汰，或所有缓存共用 TTL
- **缺失**：无缓存注解或配置

### 2.7 重试（框架级）

| 搜索模式 | 检查内容 |
|---------|---------|
| `@Retryable\(` | Spring Retry 注解 |
| `@Recover` | 重试耗尽后的恢复方法 |
| `import org\.springframework\.retry` | Spring Retry 依赖 |
| `RetryTemplate` | 编程式重试配置 |

- **已具备**：幂等操作上有 `@Retryable`，定义了 `@Recover`，指数退避已配置
- **部分具备**：有 `@Retryable` 但无 `@Recover`，或对非幂等操作重试
- **缺失**：无重试机制

### 2.8 链路追踪

| 搜索模式 | 检查内容 |
|---------|---------|
| `import io\.opentelemetry` | OpenTelemetry SDK |
| `@WithSpan\(` 或 `@SpanTag\(` 或 `@NewSpan\(` | 自定义 Span 注解 |
| `brave\.Tracer` 或 `spring-cloud-starter-sleuth` | Sleuth（旧版）|
| `tracer\.nextSpan\(\)` 或 `tracer\.currentSpan\(\)` | 编程式 Span 创建 |

- **已具备**：OTel/Sleuth 已配置，关键方法有 `@WithSpan`，自定义 Span 含业务标签
- **部分具备**：仅自动埋点；无自定义 Span 或业务标签
- **缺失**：无追踪埋点

### 2.9 线程池与异步

| 搜索模式 | 检查内容 |
|---------|---------|
| `@Async\(` | 异步方法 |
| `@EnableAsync` | 异步开关 |
| `ThreadPoolTaskExecutor` | 自定义线程池配置 |
| `RejectedExecutionHandler` | 拒绝策略 |
| `setCorePoolSize\(` 或 `setMaxPoolSize\(` | 线程池大小配置 |

- **已具备**：自定义 `ThreadPoolTaskExecutor`，有界队列，明确的拒绝策略，指标集成
- **部分具备**：`@Async` 使用默认 `SimpleAsyncTaskExecutor`
- **缺失**：无异步支持或线程池配置

### 2.10 配置管理

| 搜索模式 | 检查内容 |
|---------|---------|
| `@ConfigurationProperties\(` | 类型化配置 |
| `@RefreshScope` | 动态配置刷新 |
| 配置类上的 `@Validated` | 配置校验 |
| `@ConditionalOnProperty\(` | 特性开关 |
| `application-{profile}\.yml` | 环境特定配置 |

- **已具备**：`@ConfigurationProperties` 带校验，`@RefreshScope` 用于动态配置，特性开关
- **部分具备**：大量使用 `@Value`，无校验，所有环境共用配置
- **缺失**：硬编码常量，无外部化配置

### 2.11 API 版本化

| 搜索模式 | 检查内容 |
|---------|---------|
| `@RequestMapping` 中的 `/v[0-9]+/` | URL 路径版本化 |
| `X-API-Version` 或 `Accept-Version` 请求头 | 请求头版本化 |
| Controller 方法上的 `@Deprecated` | 废弃标记 |
| `@JsonIgnoreProperties\(ignoreUnknown = true\)` | 向下兼容 |

- **已具备**：多个 API 版本共存，废弃标记，向下兼容的 DTO
- **部分具备**：单版本，部分废弃标记
- **缺失**：无版本化策略

### 2.12 优雅关闭

| 搜索模式 | 检查内容 |
|---------|---------|
| `server\.shutdown\s*[=:]\s*graceful` | 优雅关闭开关 |
| `spring\.lifecycle\.timeout-per-shutdown-phase` | 关闭超时 |
| `@PreDestroy` | 清理钩子 |

- **已具备**：优雅关闭启用且超时合理，`@PreDestroy` 清理，就绪探针联动
- **部分具备**：优雅关闭启用但超时过短或无清理钩子
- **缺失**：默认立即关闭

### 2.13 安全 DFX

| 搜索模式 | 检查内容 |
|---------|---------|
| `RateLimiter` 或 `RateLimit` 过滤器 | API 限流 |
| `@Async` 中的 `SecurityContextHolder` 传递 | 异步上下文传递 |
| `CorsConfigurationSource` 或 `@CrossOrigin` | CORS 配置 |
| `MODE_INHERITABLETHREADLOCAL` | 安全上下文传播 |

- **已具备**：公开端点有限流，认证上下文已配置传递，CORS 指定具体域名
- **部分具备**：部分端点有限流，生产环境使用通配符 CORS
- **缺失**：无限流，未考虑认证上下文传递

---

## 三、业务 DFX 能力（11 维度）

### 3.1 订单幂等性

| 搜索模式 | 检查内容 |
|---------|---------|
| 类/方法/参数名中的 `[Ii]dempoten` | 幂等概念 |
| `X-Idempotency-Key` 或 `requestId` | 客户端幂等键 |
| Redis `SETNX` 或 DB 唯一约束 | 原子检查-存储 |
| `@Scheduled` 清理幂等键 | 键过期管理 |

- **已具备**：接收幂等键，原子检查-存储，TTL 清理
- **部分具备**：接收键但非原子检查后设置
- **缺失**：无幂等机制；可能产生重复订单

### 3.2 库存锁定与释放

| 搜索模式 | 检查内容 |
|---------|---------|
| `SELECT.*FOR UPDATE` 或 `@Lock\(` | 悲观锁 |
| `Redisson` 或 `RedisLock` 或 `distributed.*lock` | 分布式锁 |
| `releaseStock` 或 `releaseInventory` 或 `unlockStock` | 库存释放 |
| `WHERE.*stock\s*>=` 或 `CHECK.*available` | SQL 层防超卖 |

- **已具备**：扣减前加锁，失败时释放，超时释放，防超卖
- **部分具备**：有锁但失败不释放或无超时
- **缺失**：无库存锁；可能超卖

### 3.3 支付事务模式

| 搜索模式 | 检查内容 |
|---------|---------|
| 支付状态枚举含状态转换 | 支付状态机 |
| `outTradeNo` 或 `transactionId` 去重 | 支付幂等 |
| `verifySign` 或 `checkSign` 或 `validateNotify` | 回调签名验证 |
| 支付对账 `@Scheduled` 任务 | 定时对账 |

- **已具备**：状态机，幂等支付，回调验证，对账
- **部分具备**：幂等支付但无验证或无对账
- **缺失**：无支付状态追踪或去重

### 3.4 分布式事务

| 搜索模式 | 检查内容 |
|---------|---------|
| `@GlobalTransactional` 或 `io\.seata` | Seata 分布式事务 |
| `@Saga` 或 Saga 编排器类 | Saga 模式 |
| `@Compensable` 或 `@Compensate` | 补偿处理器 |
| `Outbox` 或 `TransactionalOutbox` | Outbox 模式 |
| `@TransactionalEventListener` | 事务阶段事件监听 |

- **已具备**：Saga/TCC/Outbox 模式，带正确的补偿逻辑
- **部分具备**：有 `@TransactionalEventListener` 但无补偿或 Outbox
- **缺失**：无分布式事务处理；跨服务一致性无法保证

### 3.5 秒杀/高并发防护

| 搜索模式 | 检查内容 |
|---------|---------|
| Redis 库存预加载模式 | 秒杀库存预热 |
| 订单请求的 MQ 队列 | 请求排队/背压 |
| 秒杀路径的用户级限流 | 用户级限流 |
| 秒杀模块的特性开关或熔断 | 秒杀隔离/降级 |

- **已具备**：Redis 预加载，MQ 排队，用户级限流，独立模块降级
- **部分具备**：部分但非全部保护（如仅预热无 MQ）
- **缺失**：无秒杀专项防护

### 3.6 状态机监控

| 搜索模式 | 检查内容 |
|---------|---------|
| `StateMachine` 或 `squirrel-foundation` 或 `stateless4j` | 状态机库 |
| 状态枚举含正式转换校验 | 结构化状态转换 |
| `@Scheduled` 卡单检测任务 | 滞留状态告警 |
| 每个状态转换的 `Counter` | 状态转换指标 |

- **已具备**：正式状态机，卡单检测，转换指标
- **部分具备**：枚举状态但临时转换（if/else）
- **缺失**：无正式状态管理；原始状态字段

### 3.7 第三方服务降级

| 搜索模式 | 检查内容 |
|---------|---------|
| 外部服务的 `interface.*Client` 或 `interface.*Gateway` | 外部服务抽象 |
| 每个外部服务调用上的 `@CircuitBreaker` | 每服务独立熔断 |
| 返回缓存/降级响应的降级实现 | 优雅降级 |
| 外部服务接口的多实现 | 供应商故障转移 |

- **已具备**：接口抽象，每服务独立熔断，降级实现，多供应商
- **部分具备**：有接口但无降级或熔断
- **缺失**：直接调用外部服务，无抽象和保护

### 3.8 业务告警指标

| 搜索模式 | 检查内容 |
|---------|---------|
| 含业务事件名的 `Counter\.builder\(` | 业务 KPI 计数器 |
| 指标名或配置中的 `alert` 前缀 | 告警阈值配置 |
| 指标中的 SLA/SLI 计算 | SLO 追踪 |
| 告警阈值的 `@ConfigurationProperties` | 可配置告警阈值 |

- **已具备**：定义了业务 KPI，告警阈值已配置，追踪 SLI
- **部分具备**：有些业务指标但无告警或阈值
- **缺失**：无业务级指标；仅系统指标

### 3.9 用户旅程/漏斗追踪

| 搜索模式 | 检查内容 |
|---------|---------|
| `AnalyticsEvent` 或 `FunnelEvent` 或 `UserActionEvent` | 结构化分析事件 |
| 在转化节点（浏览、加购、结算、支付）发布事件 | 漏斗各步骤事件 |
| 漏斗转化 `Counter` 指标 | 漏斗转化率 |

- **已具备**：所有漏斗节点有结构化事件，转化指标
- **部分具备**：部分漏斗节点有事件；缺转化指标
- **缺失**：无用户旅程追踪

### 3.10 超时管理

| 搜索模式 | 检查内容 |
|---------|---------|
| `@Transactional\(timeout` 按操作区分 | 按操作 DB 超时 |
| `RestTemplate` 或 `WebClient` 超时配置 | HTTP 客户端超时 |
| 带名称的 `@TimeLimiter\(` | Resilience4j 时间限制器 |
| `spring\.lifecycle\.timeout-per-shutdown-phase` | 关闭超时 |

- **已具备**：按操作类型区分超时，超时后升级处理
- **部分具备**：所有操作共用全局超时
- **缺失**：无超时配置；默认无限等待

### 3.11 数据一致性对账

| 搜索模式 | 检查内容 |
|---------|---------|
| `@Scheduled` 对账/比对任务 | 定时对账 |
| 类名中的 `reconcil` 或 `settlement` 或 `consistency.*check` | 对账逻辑 |
| 跨系统比对逻辑（本地 vs 网关）| 一致性检查 |
| `@Scheduled` 失败重试任务 | 补偿重试 |

- **已具备**：定期对账，失败重试，不匹配告警
- **部分具备**：有对账但手动触发或覆盖不全
- **缺失**：无跨系统一致性检查

---

## 分类评定标准

所有维度统一适用以下标准：

### 已具备（评分 1.0）
- 模式在 3 处以上出现，或出现在专门的配置类中
- 跨模块一致应用的证据
- 配置或集成可见（配置类、properties、bootstrap）
- 配套机制齐全（如熔断有降级，缓存有淘汰）

### 部分具备（评分 0.5）
- 模式仅在 1-2 处出现
- 跨模块应用不一致
- 有注解但缺配置
- 有模式但缺配套
- 有依赖但无自定义配置

### 缺失（评分 0.0）
- 未找到相关 import、注解或配置
- 该 DFX 关注点在代码中未得到任何处理

---

## 各维度风险等级

用于仪表盘报告中风险汇总排序。

**高风险**：分布式事务(3.4)、秒杀防护(3.5)、支付事务(3.3)、库存锁(3.2)、订单幂等(3.1)

**中风险**：熔断(2.5)、重试(2.7)、缓存(2.6)、超时管理(3.10)、指标监控(2.3)、异步线程(2.9)、安全DFX(2.13)、业务告警(3.8)

**低风险**：日志(2.1)、异常(2.2)、健康检查(2.4)、链路追踪(2.8)、配置管理(2.10)、API版本(2.11)、优雅关闭(2.12)、状态机(3.6)、第三方降级(3.7)、漏斗(3.9)、对账(3.11)
