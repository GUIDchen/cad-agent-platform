# Contributing

感谢参与。提交前请先开 issue 描述问题/方案，避免大改动返工。

## 开发环境

~~~bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd frontend && npm ci
~~~

## 提交前检查

~~~bash
.venv/bin/ruff check backend tests tools
.venv/bin/pytest -q
cd frontend && npm run build && npm run e2e
~~~

## 约定

- 使用约定式提交：feat/fix/docs/test/chore/refactor。
- 每个 PR 只做一件事；附测试与复现步骤。
- 不提交密钥、真实企业数据、构建产物、备份文件。
- 外部适配器改动请在 PR 描述中注明测试环境；未验证的能力不要写成已验证。
- 新功能需同步 README/docs 与 CHANGELOG。

## 代码风格

- Python：ruff，类型标注优先。
- Vue：Composition API，Element Plus 按需引入。
- 测试：pytest + Playwright；关键路径必须有测试。
