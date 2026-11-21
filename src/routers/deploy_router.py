from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/api/deploy", tags=["deploy"])
"""

class DeployReq(BaseModel):
    host: str; username: str; key_path: str
    script_path: str; args: str = ""

@router.post("/start")
async def start(req: DeployReq):
    job_id, log_path = await deploy_log.start_deploy(
        req.host, req.username, req.key_path, req.script_path, req.args)
    return {"job_id": job_id, "log_file": str(log_path)}

@router.get("/jobs")
async def jobs(limit: int = 50, offset: int = 0):
    return await db.list_jobs(limit, offset)

@router.post("/retention/run")
async def run_retention():
    await retention.archive_and_clean()
    return {"ok": True}
"""