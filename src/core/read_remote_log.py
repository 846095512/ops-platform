import asyncio
import time

from src.core.config import settings

# 行数缓存：host:path -> (count, ts)
_count_cache: dict[str, tuple[int, float]] = {}
_count_locks: dict[str, asyncio.Lock] = {}


def _clip(line: str) -> str:
    line = line.rstrip("\r\n")
    return line[:] + " …" if len(line) > settings.max_line_chars else line


async def _count_lock(key):
    if key not in _count_locks:
        _count_locks[key] = asyncio.Lock()
    return _count_locks[key]


async def get_total_lines(conn, host: str, path: str, force=False) -> int:
    """用 wc -l 拿总行数，缓存 TTL 内复用。"""
    key = f"{host}:{path}"
    lock = await _count_lock(key)
    async with lock:
        cached = _count_cache.get(key)
        if cached and not force and time.time() - cached[1] < settings.line_count_ttl_sec:
            return cached[0]
        result = await conn.run(f"wc -l < {_q(path)}", check=True, timeout=30)
        n = int(result.stdout.strip() or 0)
        _count_cache[key] = (n, time.time())
        return n


def _q(s: str) -> str:
    """单引号转义，防命令注入。"""
    return "'" + s.replace("'", "'\\''") + "'"

'''
async def read_page(host, username, key_path, path, start_line=1,
                    want=settings.default_page_lines) -> dict:
    """
    按行号范围读一屏。用 sed -n 'X,Yp' 让远程机完成定位。
    start_line 1-based，返回 {lines:[{line_no,text}], start,end,total,has_more}
    """
    want = min(max(1, want), settings.max_page_lines)
    start_line = max(1, start_line)
    end_line = start_line + want - 1
    conn = await pool.get(host, username, key_path)

    total = await get_total_lines(conn, host, path)
    if total == 0:
        return {"lines": [], "start": 0, "end": 0, "total": 0, "has_more": False}

    start_line = min(start_line, total)
    end_line = min(end_line, total)
    cmd = f"sed -n '{start_line},{end_line}p' {_q(path)}"
    result = await conn.run(cmd, check=True, timeout=60)
    raw_lines = result.stdout.splitlines()
    lines = [{"line_no": start_line + i, "text": _clip(t)} for i, t in enumerate(raw_lines)]
    return {
        "lines": lines,
        "start": start_line, "end": start_line + len(lines) - 1,
        "total": total, "has_more": end_line < total,
    }


async def search(host, username, key_path, path, keyword,
                 max_results=settings.max_search_lines) -> dict:
    """
    grep -n 搜索，只返回命中行。结果按行号升序。
    不做分页游标：单页 max_results 上限，超出提示用户加精确关键词。
    """
    if not keyword.strip():
        raise ValueError("关键字不能为空")
    conn = await pool.get(host, username, key_path)
    # grep -n 输出格式：行号:内容
    cmd = f"grep -n -- {_q(keyword)} {_q(path)} | head -n {max_results + 1}"
    result = await conn.run(cmd, check=False, timeout=120)  # grep 无命中返回 1
    hits = []
    for line in result.stdout.splitlines():
        if ":" not in line: continue
        no_str, text = line.split(":", 1)
        try:
            no = int(no_str)
        except ValueError:
            continue
        hits.append({"line_no": no, "text": _clip(text)})
    truncated = len(hits) > max_results
    return {"results": hits[:max_results], "truncated": truncated}
'''