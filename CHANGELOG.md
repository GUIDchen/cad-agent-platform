# Changelog

## v0.62.0 (2026-10)

### Docs

- 最终项目审阅与完成度

## v0.61.0 (2026-10)

### Added

- DXF 倒角参数 chamfer

### Changed

- 测试 138 → 139

## v0.60.0 (2026-10)

### Added

- 外部向量检索后端（VECTOR_SEARCH_URL）
- 外部异常回退本地块级检索

### Changed

- 测试 136 → 138

## v0.59.0 (2026-10)

### Added

- 批量任务进度弹窗与轮询

### Changed

- CAD 批量 UI 92% → 94%

## v0.58.0 (2026-10)

### Added

- RAG 块级向量 JSONL 导出

### Changed

- 测试 135 → 136

## v0.57.0 (2026-10)

### Added

- 备份完整性校验工具

### Changed

- 测试 133 → 135

## v0.56.0 (2026-10)

### Added

- ComfyUI 工作流加载校验（节点/占位符）

### Changed

- 测试 132 → 133

## v0.55.0 (2026-10)

### Added

- 回收站保留期清理工具

### Changed

- 测试 131 → 132

## v0.54.0 (2026-10)

### Added

- RAG 回收站/软删除/恢复/彻底删除

### Changed

- 测试 130 → 131

## v0.53.0 (2026-10)

### Added

- RAG 文档版本快照/历史/恢复
- 知识库历史弹窗

### Changed

- 测试 129 → 130

## v0.52.0 (2026-10)

### Added

- AI 绘图 negative_prompt/seed
- ComfyUI 工作流 NEGATIVE/SEED 占位符

### Changed

- 测试 128 → 129

## v0.51.0 (2026-10)

### Added

- RAG 文档删除 API
- 知识库删除 UI 与块清理

### Changed

- 测试 127 → 128

## v0.50.0 (2026-10)

### Added

- RAG 文档编辑 API
- 知识库编辑 UI 与即时重建

### Changed

- 测试 126 → 127

## v0.49.0 (2026-10)

### Added

- RAG content_hash 与增量重建
- force 全量重建参数

### Changed

- 测试 125 → 126

## v0.48.0 (2026-10)

### Added

- CAD 参考适配器 example_adapter
- 适配器契约文档（Windows COM 说明）

### Changed

- 测试 124 → 125

## v0.47.0 (2026-10)

### Added

- RAG stats/reindex API
- 知识库重建索引按钮

### Changed

- 测试 123 → 124

## v0.46.0 (2026-10)

### Added

- 图纸批量选择与统一参数生成 UI

### Changed

- 批量能力从 API 扩展到界面

## v0.45.0 (2026-10)

### Added

- 轮廓内孔/槽/开口包含校验

### Changed

- 测试 122 → 123

## v0.44.0 (2026-10)

### Added

- CAD 批量出图 API（最多 20 张）
- 批量锁/权限/状态校验与审计

### Changed

- 测试 121 → 122

## v0.43.0 (2026-10)

### Added

- DXF 异形轮廓 outline
- 轮廓边界校验与前端输入

### Changed

- 测试 120 → 121

## v0.42.0 (2026-10)

### Added

- knowledge_chunks 表与切分
- 块级向量/关键词检索

### Changed

- 测试 119 → 120

## v0.41.0 (2026-10)

### Added

- DXF 矩形开口 cutouts（CUT 图层）
- 详情开口输入与 i18n

### Changed

- 测试 117 → 119

## v0.40.0 (2026-10)

### Added

- ComfyUI 工作流校验工具
- 死信清空 API/运维操作

### Changed

- 测试 114 → 117

## v0.39.0 (2026-10)

### Added

- DXF 腰形槽参数
- 详情表单/时间/槽位 i18n

### Changed

- 测试 113 → 114

## v0.38.0 (2026-10)

### Added

- 详情表单/日期 i18n
- 版本 diff 表头 i18n

### Changed

- 核心攻坚 Git 阶段 3–5 完成

## v0.37.0 (2026-10)

### Added

- 详情页主标签 i18n
- DXF 圆角参数

### Changed

- 测试 112 → 113

## v0.36.0 (2026-10)

### Added

- i18n 扩展到项目/用户/审计/知识库/绘图/助手

### Changed

- 详情页 i18n 仍待补

## v0.35.0 (2026-10)

### Added

- 远程 embedding 与失败降级
- Rerank 接口与失败降级

### Changed

- 测试 108 → 112

## v0.34.0 (2026-10)

### Added

- 死信任务列表/重排 API
- /ops 运维页

### Changed

- 测试 107 → 108

## v0.33.0 (2026-10)

### Added

- 图纸/审批页中英文案
- CAD 适配器契约验收

### Changed

- 核心攻坚阶段 1–5 完成

## v0.32.0 (2026-10)

### Added

- 队列死信与自动重试（JOB_MAX_ATTEMPTS）
- 备份恢复演练工具
- 向量 RAG（本地 hash，可替换 embedding API）
- CAD 适配器契约验收工具

### Changed

- 测试 100 → 107

## v0.31.0 (2026-10)

### Docs

- 阶段 E 全量审阅与完成度报告
- 面试文档/PDF 更新到 100 tests、15 E2E、61 routes、11 tables

## v0.30.0 (2026-10)

### Added

- 知识库文档与关键词检索（RAG 接口）
- 中英基础 i18n 与语言切换

### Changed

- 测试 99 → 100；E2E 12 → 15

## v0.29.0 (2026-10)

### Added

- Pinia auth/notifications
- TanStack Query 图纸/审批/看板
- 创建/审批 mutation 与缓存失效

### Changed

- 入口 JS +55 KB（gzip +17 KB）

## v0.28.0 (2026-10)

### Added

- 深色模式
- 命令面板（Ctrl/Cmd+K）
- 图纸列表骨架屏
- 移动端表格优化

### Changed

- E2E 9 → 12

## v0.27.0 (2026-10)

### Added

- 队列 processing/ack/requeue
- 任务取消/重试 API 与前端按钮

### Changed

- 测试 98 → 99

## v0.26.0 (2026-10)

### Added

- Redis 持久任务队列与 worker
- Compose worker 服务
- queue 执行模式

### Changed

- 测试 97 → 98

## v0.25.0 (2026-10)

### Added

- 通知中心（表/API/铃铛/未读）
- 图纸评论与讨论
- 通知/评论迁移

### Changed

- 测试 95 → 97

## v0.24.0 (2026-10)

### Added

- Element Plus 按需引入、路由懒加载
- SSE 任务进度、审批待办页
- 版本对比、版本 PDF 导出
- 拖拽上传、统一 PageHeader

### Changed

- 测试 92 → 95

## v0.23.0 (2026-10)

### Added

- 审计 IP 与 request_id 上下文
- 项目成员角色 PATCH 与前端下拉
- 404 页面
- 图纸 X-Total-Count
- Compose Redis 健康检查/重启策略

### Changed

- 测试 91 → 92

### Docs

- 新增面试介绍与问答（技术方案、成本、设备、工期、35 问）

## v0.22.0 (2026-10)

### Added

- 安全响应头
- 上传大小与 DXF 结构校验
- 图纸过滤/分页
- 登录审计
- Redis 就绪检查
- /api/version
- 审批状态图、移动端详情响应式
- ruff lint 与 CI

### Changed

- 测试 85 → 91

## v0.21.0 (2026-10)

### Added

- 外部联调检查器与手册
- WebKit E2E
- 无障碍基础与 E2E 断言

### Changed

- 测试 84 → 85；E2E 2 → 9

## v0.20.0 (2026-10)

### Added

- 侧边栏应用壳、移动端抽屉、面包屑
- 登录页 Hero 重设计
- 看板 KPI + ECharts 环形图
- 图纸搜索/统计/空状态
- 数据库索引迁移与 SQLite WAL/连接池
- Vite vendor 分包

## v0.19.0 (2026-10)

### Added

- 全局 IP 限流（默认 240/分钟）

### Changed

- 尝试 Firefox/WebKit，因环境问题回退 Chrome 双端
- 测试 83 → 84

## v0.18.0 (2026-10)

### Added

- CSRF 双提交 Cookie 防护
- 上传病毒扫描（mock/ClamAV）
- ERP/BOM 推送（mock/webhook）

### Changed

- 测试 80 → 83

## v0.17.0 (2026-10)

### Added

- DWG→DXF 转换与 DWG 上传
- 备份恢复工具与 cron 示例
- Agent 工具调用（LLM/兜底）与助手页
- ComfyUI 工作流适配

### Changed

- 测试 69 → 80

## v0.16.0 (2026-10)

### Added

- AI 绘图接口 `/api/ai/image`（mock/远程）
- 前端绘图页 `/images`
- AI 接口限流（Redis/内存）
- CAD 适配器契约文档

### Changed

- 测试 67 → 69

## v0.15.0 (2026-10)

### Added

- 存量 DXF 上传（API + 前端）
- 备份工具 `tools/backup.py`
- AI 参数解析（LLM 兼容接口 + 规则兜底）
- Redis 状态外置（重放/指标）
- 生产配置启动校验

### Changed

- 审批/BOM/生成/上传下沉到 services
- drawings/generation/bom/system/spa 路由拆分
- 每个测试独立重置数据库
- 测试 59 → 67

## v0.14.0 (2026-10)

### Added

- `POST /api/wecom/event` 事件回调
- 卡片 approve/reject 动作路由
- 内存 TTL 重放保护
- 测试 55 → 58

## v0.13.0 (2026-10)

### Added

- 企业微信 AES 加解密与 SHA1 验签
- `GET /api/wecom/verify` 回调 URL 验证
- 测试 51 → 55

## v0.12.0 (2026-10)

### Added

- Alertmanager 配置与 Compose 服务
- `POST /api/alerts` 告警 Webhook
- 告警 firing/resolved 通知
- 测试 50 → 51

## v0.11.0 (2026-10)

### Added

- Prometheus 抓取配置与 3 条告警规则
- Grafana 数据源与 CAD 看板（自动 provisioning）
- Compose 增加 prometheus/grafana

## v0.10.0 (2026-10)

### Added

- 请求 ID 中间件与 Prometheus 指标
- 审计保留期清理工具

### Changed

- 测试 48 → 50

## v0.9.0 (2026-10)

### Added

- Playwright 桌面/移动双端矩阵
- S3 存储 moto 测试
- `backend/requirements-dev.txt`

### Changed

- 测试 47 → 48；E2E 1 → 2

## v0.8.0 (2026-10)

### Added

- SPA 路由回退（/login、/drawings/:id）
- Playwright E2E：设计员生成 → 审批人通过
- CI e2e job

## v0.7.0 (2026-10)

### Added

- `POST /api/wecom/action` 卡片动作转发
- 存储健康检查与 `/api/ready` 503 降级
- Compose api healthcheck / web 依赖 healthy
- `tools/check_storage.py`
- 测试 44 → 47

## v0.6.0 (2026-10)

### Added

- 审计 start/end 时间范围过滤（API + 前端）
- 通知死信文件与 `tools/retry_notifications.py` 重试
- 企业微信审批卡片构造
- 测试 42 → 44

## v0.5.0 (2026-10)

### Added

- 前端审计页 `/audit` 与 CSV 导出
- 项目成员变更通知
- Alembic 基线迁移与 `tests/test_migrations.py`
- 测试 40 → 42

## v0.4.0 (2026-10)

### Added

- 前端 `/projects` 成员管理与 `/users` 用户管理
- 通知模块（mock 文件 / 企业微信 Webhook）
- 审计 `action`/`actor_id` 过滤、分页、CSV 导出
- `GET /users/options`
- 测试 36 → 40

## v0.3.0 (2026-10)

### Added

- 项目成员表与项目级访问控制
- 用户管理 API（创建、改角色、启停）
- `/api/ready` 就绪检查
- GitHub Actions CI（后端测试 + 前端构建）
- 外部依赖登记表
- 测试 27 → 36

## v0.2.0 (2026-10)

### Added

- 存储抽象：local / S3(MinIO)，版本文件改为 object key
- 会话 Cookie + 企业微信 SSO（mock/real）
- Worker 任务分发：bracket / solidworks / altium 外部适配器
- `GET /api/stats` 与前端看板
- 测试 17 → 27

### Changed

- `GenerateIn` 增加 `job_type`
- Compose 增加 MinIO 与相关环境变量

## v0.1.1 (2026-10)

### Added

- `GET /api/drawings/{id}/bom` 导出 CSV
- 前端“导出 BOM”按钮
- `tests/test_bom.py`（2 个用例）

### Changed

- 测试总数 11 → 13

## v0.1.0 (2026-10)

### Added

- SDLC 文档 00–12
- FastAPI 后端：登录、项目、图纸、生成、版本、审批、锁、审计
- ezdxf 生成器、校验器、PNG 预览
- inline / external 两种执行模式与 Worker
- Vue3 + Element Plus 前端
- pytest 11 个用例
- Docker Compose 部署
