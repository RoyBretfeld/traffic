# backend/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uuid, time
import logging

logger = logging.getLogger(__name__)

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        request.state.correlation_id = cid
        start = time.perf_counter()
        try:
            resp = await call_next(request)
        except Exception as e:
            logger.exception("Unhandled error", extra={"correlation_id": cid})
            resp = JSONResponse(status_code=500, content={
                "error": "internal_error",
                "message": str(e),
                "correlation_id": cid,
            })
        dur = (time.perf_counter() - start) * 1000
        resp.headers["x-correlation-id"] = cid
        resp.headers["x-duration-ms"] = f"{dur:.2f}"
        return resp
