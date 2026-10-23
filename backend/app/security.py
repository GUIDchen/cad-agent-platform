from .config import ALLOW_DEV_AUTH, APP_ENV, SECRET_KEY, WECOM_ENCODING_AES_KEY, WECOM_MODE, WECOM_TOKEN


def validate_config() -> None:
    if APP_ENV != "production":
        return
    problems: list[str] = []
    if not SECRET_KEY or SECRET_KEY == "dev-secret-change-me":
        problems.append("生产环境必须设置非默认 SECRET_KEY")
    if ALLOW_DEV_AUTH:
        problems.append("生产环境必须设置 ALLOW_DEV_AUTH=false")
    if WECOM_MODE == "real" and (not WECOM_TOKEN or not WECOM_ENCODING_AES_KEY):
        problems.append("WECOM_MODE=real 时必须配置 WECOM_TOKEN/WECOM_ENCODING_AES_KEY")
    if problems:
        raise RuntimeError("; ".join(problems))
