# DFX 报告数据结构 (JSON Schema)

本文件定义了 `dfx-report.html` 所需的 `__REPORT_DATA__` JSON 结构。

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
        { 
          "name": "订单处理", 
          "detected": true, 
          "fileCount": 28, 
          "keyClasses": ["OrderService.java", "OrderController.java"] 
        }
      ],
      "genericDFX": [
        { 
          "id": "2.1", 
          "name": "日志诊断", 
          "status": "present", 
          "score": 1.0,
          "summary": "SLF4J + MDC 上下文完整配置，LogstashEncoder 已启用", 
          "evidence": ["LogConfig.java", "OrderService.java"], 
          "recommendations": [] 
        }
      ],
      "businessDFX": [
        { 
          "id": "3.1", 
          "name": "订单幂等", 
          "status": "partial", 
          "score": 0.5,
          "summary": "接收 X-Idempotency-Key 但未使用 SETNX 原子操作", 
          "evidence": ["OrderController.java"], 
          "recommendations": ["使用 Redis SETNX 实现强幂等"] 
        }
      ],
      "scores": { 
        "overall": 0.72, 
        "genericDFX": 0.68, 
        "businessDFX": 0.76, 
        "confidence": "high" 
      },
      "remediation": [
        { 
          "priority": "P0", 
          "phase": "快速见效", 
          "dimensionId": "2.12", 
          "dimensionName": "优雅关闭",
          "action": "在 application.yml 中添加 server.shutdown=graceful", 
          "targetFiles": ["application.yml"], 
          "codePattern": "server:\n  shutdown: graceful\n  lifecycle:\n    timeout-per-shutdown-phase: 30s", 
          "effort": "2min", 
          "impact": "部署时请求不丢失" 
        }
      ]
    }
  ],
  "crossService": {
    "ranking": ["order-service", "payment-service", "inventory-service"],
    "comparisonMatrix": {
      "order-service": { "overall": 0.72, "genericDFX": { "2.1": 1.0, "2.2": 0.5 }, "businessDFX": { "3.1": 0.5 } }
    },
    "commonGaps": [
      { "dimensionId": "2.8", "dimensionName": "链路追踪", "affectedCount": 3, "totalServices": 3 }
    ]
  }
}
```
