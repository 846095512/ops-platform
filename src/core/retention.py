import gzip
import shutil
import time
from pathlib import Path

from src.core.config import settings


async def archive_and_clean(deploy_log_dir: Path):
    """
    每天跑一次：
    1. 超过 KEEP_DAYS 的 .log → gzip 压缩为 .log.gz
    2. 压缩后仍超 MAX_BYTES 的，从最旧的开始删
    """
    now = time.time()
    cutoff = now - settings.deploy_log_keep_days * 86400
    logs = sorted(deploy_log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime)

    for p in logs:
        if p.stat().st_mtime < cutoff:
            gz = p.with_suffix(".log.gz")
            with open(p, "rb") as fi, gzip.open(gz, "wb") as fo:
                shutil.copyfileobj(fi, fo)
            p.unlink()

    # 大小清理
    total = 0
    files = sorted(deploy_log_dir.glob("*"), key=lambda p: p.stat().st_mtime)
    for p in files:
        total += p.stat().st_size
    while total > settings.deploy_log_max_bytes and files:
        oldest = files.pop(0)
        total -= oldest.stat().st_size
        oldest.unlink()
