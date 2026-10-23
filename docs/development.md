# 开发

## 环境

- Python 3.12
- Node.js 22
- SQLite（默认）或 PostgreSQL
- Redis（队列可选；默认内存模式）

## 启动

~~~bash
cp backend/.env.example backend/.env
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
.venv/bin/uvicorn app.main:app --app-dir backend --reload --port 8000
~~~

前端：

~~~bash
cd frontend
npm ci
npm run dev
~~~

## 测试

~~~bash
.venv/bin/pytest -q
.venv/bin/ruff check backend tests tools
cd frontend && npm run build && npm run e2e
~~~

E2E 使用 Playwright，覆盖 Chrome 桌面/移动与 WebKit；首次需 npx playwright install。

## 迁移

~~~bash
.venv/bin/alembic upgrade head
~~~

## 约定

- Python 使用 ruff；Vue 使用 Composition API。
- API 变更同步 docs/api.md。
- 外部适配器未验证时，文档中明确标注。
