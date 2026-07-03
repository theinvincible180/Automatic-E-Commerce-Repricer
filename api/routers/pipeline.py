import asyncio
import sys
import os
import time
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# Simple in-memory flag to track pipeline state
# In production this would live in Redis or the DB
pipeline_status = {"running": False, "last_run": None}


@router.get("/status")
def get_status():
    """Returns whether the pipeline is currently running."""
    return pipeline_status


@router.get("/run")
def run_pipeline():
    """
    Triggers a full pipeline run and streams log output
    back to the frontend line by line using Server-Sent Events.

    SSE (Server-Sent Events): instead of the frontend waiting
    60 seconds for a response, the server streams each line as
    it's produced. The browser receives and renders each line
    in real time — like a live terminal in the browser.
    """
    if pipeline_status["running"]:
        return {"error": "Pipeline is already running."}

    def stream():
        pipeline_status["running"] = True

        try:
            sys.path.insert(0, os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))

            from run_pipeline import run_full_pipeline
            import io
            from contextlib import redirect_stdout

            yield "data: Starting pipeline...\n\n"

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                run_full_pipeline()

            for line in buffer.getvalue().splitlines():
                yield f"data: {line}\n\n"
                time.sleep(0.03)

            pipeline_status["last_run"] = datetime.now().isoformat()
            yield "data: [DONE] Pipeline complete.\n\n"

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

        finally:
            pipeline_status["running"] = False

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )