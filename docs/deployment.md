# 部署

## Docker Compose

~~~bash
cd deploy
cp ../backend/.env.example .env
docker compose up -d --build
~~~

包含 api、worker、postgres、redis、prometheus、grafana（以 compose 文件为准）。

## 生产必改

| 变量 | 要求 |
|---|---|
| APP_ENV | production |
| ALLOW_DEV_AUTH | false |
| SECRET_KEY | 强随机值 |
| DATABASE_URL | PostgreSQL |
| REDIS_URL | Redis |
| STORAGE_BACKEND | local 或 s3 |
| EXECUTION_MODE | queue（配 worker） |

## 健康检查

~~~bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/version
~~~

## 备份

~~~bash
.venv/bin/python tools/backup.py --out backups
.venv/bin/python tools/backup_verify.py backups/backup-xxxx
.venv/bin/python tools/restore_drill.py --backup backups/backup-xxxx
~~~

## 监控

- /metrics Prometheus
- deploy/prometheus、deploy/grafana
- 告警规则见 deploy/prometheus/alerts.yml
