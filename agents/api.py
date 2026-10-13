"""FastAPI service and optional local web console."""
import hmac
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .base import AuditLogger
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
REPO_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="ZK-STARK FRI Agent API",
    description="Educational parameter-audit service (not a STARK proof verifier)",
    version="3.0.1",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/", include_in_schema=False)
def index_page():
    return FileResponse(REPO_ROOT / "web" / "index.html")


@app.get("/engine.py", include_in_schema=False)
def browser_engine():
    return FileResponse(REPO_ROOT / "zk_stark_fri" / "engine.py", media_type="text/plain")


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "zk-stark-fri-prover-agent", "version": "3.0.1"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "RUNNING",
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    return supervisor.process_task(payload).to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    return {"response": supervisor.query_supervisory_chat(req.query)}


@app.get("/api/audit/logs")
def api_audit_logs(x_audit_token: Optional[str] = Header(default=None)):
    token = os.getenv("AUDIT_ADMIN_TOKEN")
    if not token or not x_audit_token or not hmac.compare_digest(x_audit_token, token):
        raise HTTPException(status_code=403, detail="Audit logs disabled or unauthorized")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
