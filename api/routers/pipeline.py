import sys
import os
import time
import threading
from queue import Queue, Empty
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from api.auth import get_current_user

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

pipeline_status = {"running": False, "last_run": None}
LOG_FILE = "pipeline.log"
MAX_LOG_SIZE = 1 * 1024 * 1024  # 1 MB log limit


def append_log(text: str):
    """Appends to the log file with basic rotation to prevent memory bloat."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

    if os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines[-1000:])


@router.get("/logs")
def get_recent_logs(lines: int = 200):
    if not os.path.exists(LOG_FILE):
        return {"logs": []}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    formatted_logs = [{"text": line.strip(), "type": "log"} for line in all_lines[-lines:]]
    return {"logs": formatted_logs}


@router.get("/status")
def get_status():
    return pipeline_status


# ── Real-time Logger Class ──────────────────────────────
class StreamLogger:
    """Intercepts print() and sends text to a live queue instantly."""
    def __init__(self, queue, original_stdout):
        self.queue = queue
        self.original_stdout = original_stdout

    def write(self, text):
        if text.strip():
            self.queue.put(text.strip())
        self.original_stdout.write(text)

    def flush(self):
        self.original_stdout.flush()
# ─────────────────────────────────────────────────────────


@router.get("/run")
def run_pipeline(token: str):
    def stream():
        if pipeline_status.get("running"):
            yield "data: [ERROR] Pipeline is already running.\n\n"
            return

        # Validate the token manually since EventSource can't send headers
        try:
            get_current_user(token)
        except Exception:
            yield "data: [ERROR] Unauthorized.\n\n"
            return

        pipeline_status["running"] = True
        original_stdout = sys.stdout

        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from agents.repricer_chain import run_repricer_chain

            start_msg = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 PIPELINE STARTED"
            append_log(start_msg)
            yield f"data: {start_msg}\n\n"

            log_queue = Queue()
            sys.stdout = StreamLogger(log_queue, original_stdout)

            task_state = {"is_done": False, "error": None}

            def background_task():
                try:
                    run_repricer_chain()
                except Exception as e:
                    task_state["error"] = str(e)
                finally:
                    task_state["is_done"] = True

            worker_thread = threading.Thread(target=background_task)
            worker_thread.start()

            while not task_state["is_done"] or not log_queue.empty():
                try:
                    line = log_queue.get(timeout=0.5)
                    append_log(line)
                    yield f"data: {line}\n\n"
                except Empty:
                    yield ": heartbeat\n\n"

            if task_state["error"]:
                err_msg = f"❌ [ERROR] {task_state['error']}"
                append_log(err_msg)
                yield f"data: {err_msg}\n\n"
            else:
                pipeline_status["last_run"] = datetime.now().isoformat()
                append_log("✅ Pipeline complete.\n")
                yield "data: [DONE] Pipeline complete.\n\n"

        except Exception as e:
            append_log(f"❌ [ERROR] {str(e)}")
            yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            sys.stdout = original_stdout
            pipeline_status["running"] = False

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )