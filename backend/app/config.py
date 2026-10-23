import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", DATA_DIR / "storage"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", DATA_DIR / "cache"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'app.db'}")
REDIS_URL = os.getenv("REDIS_URL", "")
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "inline")
WORKER_TOKEN = os.getenv("WORKER_TOKEN", "dev-worker")
ADMIN_USERS = [x.strip() for x in os.getenv("ADMIN_USERS", "admin").split(",") if x.strip()]

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_BUCKET = os.getenv("S3_BUCKET", "cad-platform")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

APP_ENV = os.getenv("APP_ENV", "dev").lower()
APP_VERSION = os.getenv("APP_VERSION", "0.62.0")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALLOW_DEV_AUTH = os.getenv("ALLOW_DEV_AUTH", "true").lower() == "true"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
CSRF_COOKIE = "csrf_token"
SESSION_COOKIE = "cad_session"
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "86400"))

WECOM_MODE = os.getenv("WECOM_MODE", "mock").lower()
WECOM_CORP_ID = os.getenv("WECOM_CORP_ID", "")
WECOM_AGENT_ID = os.getenv("WECOM_AGENT_ID", "")
WECOM_SECRET = os.getenv("WECOM_SECRET", "")
WECOM_REDIRECT_URI = os.getenv("WECOM_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/wecom/callback")
WECOM_ACTION_TOKEN = os.getenv("WECOM_ACTION_TOKEN", "dev-wecom-action")
WECOM_TOKEN = os.getenv("WECOM_TOKEN", "")
WECOM_ENCODING_AES_KEY = os.getenv("WECOM_ENCODING_AES_KEY", "")
ALERT_WEBHOOK_TOKEN = os.getenv("ALERT_WEBHOOK_TOKEN", "dev-alert-token")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-flash")
IMAGE_API_URL = os.getenv("IMAGE_API_URL", "")
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", "")
COMFY_URL = os.getenv("COMFY_URL", "")
COMFY_WORKFLOW = os.getenv("COMFY_WORKFLOW", "")
COMFY_TIMEOUT = int(os.getenv("COMFY_TIMEOUT", "120"))
ERP_WEBHOOK_URL = os.getenv("ERP_WEBHOOK_URL", "")
ERP_WEBHOOK_TOKEN = os.getenv("ERP_WEBHOOK_TOKEN", "")
GLOBAL_RATE_LIMIT = int(os.getenv("GLOBAL_RATE_LIMIT", "240"))
JOB_MAX_ATTEMPTS = int(os.getenv("JOB_MAX_ATTEMPTS", "3"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
