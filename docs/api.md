# API

Base: /api 。认证使用 Cookie；写请求需 CSRF。交互文档：/docs（Swagger）。

## 认证

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /auth/dev-login | 开发态登录 |
| POST | /auth/login | 账密登录 |
| POST | /auth/logout | 退出 |
| GET | /auth/me | 当前用户 |

## 项目/图纸

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST | /projects | 项目列表/创建 |
| GET/POST | /projects/{id}/members | 成员 |
| GET/POST | /drawings | 图纸列表/创建 |
| GET | /drawings/{id} | 详情 |
| POST | /drawings/{id}/checkout | 检出 |
| POST | /drawings/{id}/checkin | 检入 |
| GET | /drawings/{id}/versions | 版本 |
| POST | /drawings/{id}/generate | 生成 |
| POST | /drawings/batch-generate | 批量生成 |
| POST | /versions/{id}/approve | 通过 |
| POST | /versions/{id}/reject | 驳回 |

## 任务

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /jobs/{id} | 状态 |
| GET | /jobs/{id}/events | SSE |
| POST | /jobs/{id}/cancel | 取消 |
| POST | /jobs/{id}/retry | 重试 |
| GET | /jobs/dead | 死信（admin） |
| POST | /jobs/{id}/requeue | 重排（admin） |

## AI / RAG

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /ai/parse | 参数解析 |
| POST | /ai/agent | Agent |
| POST | /ai/image | 绘图 |
| GET/POST | /rag/documents | 知识库 |
| PATCH/DELETE | /rag/documents/{id} | 编辑/软删除 |
| GET | /rag/documents/{id}/versions | 历史 |
| POST | /rag/reindex | 重建索引 |
| GET | /rag/search | 检索 |

完整字段以 /docs 为准。
