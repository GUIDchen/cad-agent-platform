# Security Policy

## Supported Versions

当前仅维护最新版本。

## Reporting a Vulnerability

请通过 GitHub Security Advisories 私密报告，或联系维护者，不要公开 issue。

请提供：影响版本、复现步骤、影响范围、修复建议。我们会在 7 天内确认。

## 使用注意

- 生产必须设置强 SECRET_KEY、关闭 ALLOW_DEV_AUTH、启用 HTTPS。
- 不要把真实企业 CAD 文件、密钥、数据库备份提交到仓库。
- 外部 CAD/AI/ERP 适配器需在受控网络验证后再接入生产。
