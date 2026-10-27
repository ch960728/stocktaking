import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> None:
    """앱 로그와 uvicorn 접속/에러 로그를 logs/app.log에 5MB씩 최대 5개까지 보관한다."""
    LOG_DIR.mkdir(exist_ok=True)
    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )

    logging.getLogger().setLevel(logging.INFO)
    # uvicorn.error는 uvicorn으로 전파되므로 uvicorn.access만 따로 붙이면 중복 없이 전부 기록된다.
    for name in ("", "uvicorn", "uvicorn.access"):
        logger = logging.getLogger(name)
        if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
            logger.addHandler(handler)
