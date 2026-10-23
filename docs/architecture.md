# 架构

## 组件

~~~text
Vue 3 SPA
   | HTTPS / JSON / SSE
FastAPI
   |-- PostgreSQL / SQLite
   |-- Redis（队列、状态、限流）
   |-- 本地存储 / S3
   |-- CAD 适配器（DXF / ODA / COM）
   |-- LLM / Embedding / Rerank / ComfyUI
Worker（可选）
   |-- cad:jobs / cad:jobs:processing / cad:jobs:dead
~~~

## 关键设计

- **单体模块化**：按 api/services/core 分层，不引入微服务。
- **版本不可变**：图纸版本只追加；审批基于版本快照。
- **检出锁**：30 分钟锁，防并发覆盖。
- **任务队列**：Redis processing + ack/requeue；失败自动重试，超限进死信。
- **存储抽象**：本地目录或 S3/MinIO。
- **AI 可降级**：无模型时规则解析、mock 图、本地 hash 向量；配置后切换远程。
- **RAG**：文档 → 块 → embedding；块级检索，可接远程向量服务。

## 主要目录

| 路径 | 说明 |
|---|---|
| backend/app/api | 路由与权限 |
| backend/app/services | 生成、审批、BOM、上传 |
| backend/app/core | DXF 生成/校验/预览 |
| backend/app/worker.py | 队列 worker |
| frontend/src/views | 页面 |
| frontend/src/queries.js | TanStack Query |
| migrations/ | Alembic |
| deploy/ | Compose、监控 |
