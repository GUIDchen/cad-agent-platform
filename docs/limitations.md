# 已知限制

本仓库是**内网试点级**实现，不是完整商用交付。

## 外部系统未验证

- ODA File Converter / AutoCAD COM / SolidWorks COM / Altium AD24；
- ComfyUI、Dify、远程绘图服务；
- ERP/PLM webhook、企业微信真实回调、MinIO、ClamAV。

仓库提供适配器契约、样例适配器与验收工具，但没有真实环境测试结果。

## AI

- 未配置模型时使用规则解析与 mock 图；
- 默认 embedding 是本地字符 n-gram hash，不是语义模型；
- 远程 embedding/rerank/向量服务需要自行部署与验证。

## 工程

- i18n 已覆盖主要页面，仍有零散文案；
- 备份提供工具与演练脚本，未在生产数据执行；
- 未做容量压测、Firefox、视觉回归；
- 原生 pgvector SQL 后端未实现（支持外部向量服务）。

## 安全

- 生产必须关闭开发登录、设置强 SECRET_KEY、启用 HTTPS；
- 不要提交真实 CAD、密钥、备份。
