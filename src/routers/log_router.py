from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel


router = APIRouter(prefix="/api/logs", tags=["logs"])

class HostAuth(BaseModel):
    host: str
    username: str
    key_path: str


'''


@router.post("/remote/open")
async def remote_open(body: HostAuth, path: str = Query(...),
                      want: int = Query(200, ge=1, le=1000)):
    """点开日志：从第 1 行开始加载一屏。"""
    try:
        return await remote_log.read_page(body.host, body.username, body.key_path,
                                          path, start_line=1, want=want)
    except Exception as e:
        raise HTTPException(502, f"读取远程日志失败: {e}")

@router.post("/remote/page")
async def remote_page(body: HostAuth, path: str = Query(...),
                      start_line: int = Query(..., ge=1),
                      want: int = Query(200, ge=1, le=1000)):
    """上下翻页 / 行号跳转：传目标起始行号。"""
    return await remote_log.read_page(body.host, body.username, body.key_path,
                                      path, start_line, want)

@router.post("/remote/search")
async def remote_search(body: HostAuth, path: str = Query(...),
                        keyword: str = Query(..., min_length=1)):
    """grep 搜索，只返回命中行。"""
    return await remote_log.search(body.host, body.username, body.key_path, path, keyword)

@router.post("/remote/count")
async def remote_count(body: HostAuth, path: str = Query(...),
                       force: bool = False):
    """刷新总行数。"""
    from ssh_pool import pool
    conn = await pool.get(body.host, body.username, body.key_path)
    n = await remote_log.get_total_lines(conn, body.host, path, force=force)
    return {"total": n}

@router.get("/deploy/stream/{job_id}")
async def deploy_stream(job_id: str, last_seq: int = 0):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(subscribe(job_id, last_seq),
                             media_type="text/event-stream",
                             headers={"X-Accel-Buffering": "no"})
'''