# DFX 运维审视 Skill

扫描 **Java/Spring** 电商后端代码仓库，自动梳理业务逻辑，识别 **通用 DFX** 和 **业务 DFX** 设计模式，生成自包含的中文 **Dashboard HTML 报告**。

## 快速开始

### 1. 克隆到本地

```bash
git clone https://github.com/kodak9527/dfx-review.git
```

### 2. 配置到 Claude Code

将 `dfx-review/` 目录放到 Claude Code 的 skills 路径下（如 `~/.claude/skills/dfx-review/`）。

### 3. 使用

在 Java/Spring 项目根目录下，对 Claude Code 说：

> 帮我做 DFX 审视

或

> /dfx-review

扫描完成后，当前目录下会生成 `dfx-report.html`，用浏览器打开即可。

---

## 能做什么

### 业务逻辑梳理（12+ 个电商领域）

自动识别代码中涉及的电商业务领域。领域列表定义在 `domains.json` 中，**可按需增删**。（默认包含：订单处理、支付账单、库存管理、购物车结算、用户账户、商品目录、促销优惠券、物流配送、消息通知、秒杀抢购、评价评分、管理后台）

### 通用 DFX 审视（13 个维度）

| 维度 | 检查内容 |
|------|---------|
| 日志与诊断 | SLF4J、MDC 上下文、JSON 日志、敏感数据脱敏 |
| 异常处理 | 全局异常处理器、异常体系、统一错误响应 |
| 指标监控 | Micrometer、@Timed、自定义 Counter/Gauge |
| 健康检查 | Actuator、HealthIndicator、K8s 探针 |
| 熔断与韧性 | Resilience4j、Sentinel、降级方法 |
| 缓存 | @Cacheable/Evict、Redis TTL、缓存穿透防护 |
| 重试 | @Retryable、@Recover、指数退避 |
| 链路追踪 | OpenTelemetry、Sleuth、自定义 Span |
| 异步线程池 | @Async、ThreadPoolTaskExecutor、拒绝策略 |
| 配置管理 | @ConfigurationProperties、@RefreshScope、特性开关 |
| API 版本化 | URL/Header 版本、废弃标记、向下兼容 |
| 优雅关闭 | graceful shutdown、@PreDestroy、就绪探针 |
| 安全 DFX | 接口限流、认证上下文传递、CORS |

### 业务 DFX 审视（11 个维度）

| 维度 | 检查内容 |
|------|---------|
| 订单幂等 | 幂等键、原子存储、TTL 清理 |
| 库存锁 | 悲观锁/分布式锁、释放机制、防超卖 |
| 支付事务 | 支付状态机、回调验签、定时对账 |
| 分布式事务 | Saga/TCC/Seata、Outbox 模式、补偿逻辑 |
| 秒杀防护 | Redis 预热、MQ 排队、用户级限流 |
| 状态机监控 | 状态机库、卡单检测、转换指标 |
| 第三方降级 | 外部服务抽象、独立熔断、多供应商 |
| 业务告警 | 业务 KPI 计数器、SLA/SLI 追踪 |
| 漏斗追踪 | 转化事件、漏斗转化率 |
| 超时管理 | 按操作区分超时、超时升级 |
| 数据对账 | 定时对账、跨系统比对、失败重试 |

---

## 报告预览

生成的 HTML 报告包含：

- **径向仪表盘** — 综合 DFX 评分
- **SVG 雷达图** — 通用/业务 DFX 各维度得分可视化
- **业务领域卡片** — 检测到的电商业务模块
- **评分明细表** — 36 个维度状态（已具备/部分具备/缺失）
- **可展开详情** — 每条维度的代码证据和改进建议
- **风险汇总** — 按高/中/低风险等级排序的待改进项
- **改造路线图** — 按 P0(快速见效)/P1(核心加固)/P2(持续完善) 分组的改造任务卡片，每条指明涉及文件、代码示例、工作量和预期效果
- **首先做这三件事** — P0 中的 Top 3 快速行动项
- **暗黑/明亮主题切换** — 支持明亮和暗黑两种模式

---

## 评分算法

每个维度分三级评定：

| 等级 | 分数 | 标准 |
|------|------|------|
| 已具备 | 1.0 | 模式一致应用，配套齐全，配置完整 |
| 部分具备 | 0.5 | 模式存在但有缺口，或使用不一致 |
| 缺失 | 0.0 | 代码中未发现相关实现 |

```
综合得分 = 通用DFX × 0.50 + 业务DFX × 0.50
```

---

## 技术栈

- 纯 Claude Code 内置工具（Glob、Grep、Read、Write）
- HTML 模板零外部依赖（无 CDN，离线可用）
- SVG 原生图表渲染
- 支持 Windows / macOS / Linux

## License

MIT
