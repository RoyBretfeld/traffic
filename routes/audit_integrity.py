from fastapi import APIRouter
from fastapi.responses import JSONResponse
from tools.orig_integrity import verify

router = APIRouter()

@router.get("/audit/orig-integrity")
def audit_integrity():
    probs = verify()
    body = {"ok": len(probs)==0, "problems": probs}
    return JSONResponse(body, media_type="application/json; charset=utf-8")
