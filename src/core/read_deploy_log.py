import asyncio
import json
import uuid

from src.core.config import settings

# 内存中的 SSE 订阅者：job_id -> set[asyncio.Queue]
_subscribers: dict[str, set[asyncio.Queue]] = {}

# 实时环形缓冲（只服务断线重连回放，落盘才是真相）
_buffers: dict[str, list] = {}


def _sse(obj): return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _push(job_id, item):
    buf = _buffers.setdefault(job_id, [])
    buf.append(item)
    if len(buf) > settings.buffer_max: buf.pop(0)
    for q in list(_subscribers.get(job_id, set())):
        try:
            q.put_nowait(item)
        except asyncio.QueueFull:
            pass

"""
async def start_deploy(host, username, key_path, script_path, args=""):
    job_id = uuid.uuid4().hex
    log_path = DEPLOY_LOG_DIR / f"{job_id}.log"
    await db.create_job(job_id, host, script_path, str(log_path))
    asyncio.create_task(_run_job(job_id, host, username, key_path, script_path, args, log_path))
    return job_id, log_path


async def _run_job(job_id, host, username, key_path, script_path, args, log_path):
    conn = await pool.get(host, username, key_path)
    cmd = f"bash {script_path} {args}".strip()
    fp = open(log_path, "w", encoding="utf-8", buffering=1)  # 行缓冲
    exit_code = -1
    status = "failed"
    try:
        async with conn.create_process(cmd, term_type="ansi") as proc:
            async def pump(reader, stream):
                async for line in reader:
                    text = line.rstrip("\r\n")[:settings.max_line_chars]
                    fp.write(text + "\n")  # 落盘：平台副本，目标机删了不影响
                    _push(job_id, {"type": "line", "stream": stream, "text": text})

            await asyncio.gather(pump(proc.stdout, "stdout"), pump(proc.stderr, "stderr"))
            exit_code = await proc.wait()
            status = "success" if exit_code == 0 else "failed"
    except asyncio.TimeoutError:
        status = "timeout"
    except Exception as e:
        _push(job_id, {"type": "line", "stream": "system", "text": f"执行异常: {e}"})
    finally:
        fp.flush();
        fp.close()
        await db.finish_job(job_id, status, exit_code)
        _push(job_id, {"type": "end", "status": status, "exit_code": exit_code,
                       "log_file": str(log_path)})
        _buffers.pop(job_id, None)


async def subscribe(job_id, last_seq=0):
   SSE 生成器。先回放缓冲增量，再等实时，最后收 end 哨兵
    q = asyncio.Queue(maxsize=1000)
    _subscribers.setdefault(job_id, set()).add(q)
    try:
        for item in _buffers.get(job_id, []):
            if item.get("seq", 0) > last_seq:
                yield _sse(item)
        while True:
            try:
                item = await asyncio.wait_for(q.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ": ping\n\n";
                continue
            if item.get("type") == "end":
                yield _sse(item);
                break
            yield _sse(item)
    finally:
        _subscribers.get(job_id, set()).discard(q)
"""