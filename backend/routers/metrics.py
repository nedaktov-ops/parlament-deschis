"""API Metrics Endpoint for Observability.

Provides Prometheus-formatted metrics for monitoring.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/api")

# In-memory metrics store (simple implementation)
_metrics: dict[str, Any] = {
    "request_count": 0,
    "start_time": datetime.now().isoformat(),
}


@router.get("/metrics")
async def metrics(request: Request) -> PlainTextResponse:
    """Return Prometheus-formatted metrics."""
    _metrics["request_count"] += 1

    lines = [
        "# HELP parlament_deschis_request_count Total number of requests",
        "# TYPE parlament_deschis_request_count counter",
        f"parlament_deschis_request_count {_metrics['request_count']}",
        "",
        "# HELP parlament_deschis_start_time Service start time (ISO 8601)",
        "# TYPE parlament_deschis_start_time gauge",
        'parlament_deschis_start_time{mode="iso"} 1',
        "",
        "# HELP parlament_deschis_build_info Build information",
        "# TYPE parlament_deschis_build_info gauge",
        'parlament_deschis_build_info{version="dev"} 1',
    ]
    return PlainTextResponse("\n".join(lines), media_type="text/plain")
