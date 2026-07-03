import sys
import os
import time
import threading
from queue import Queue, Empty
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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

# ── NEW: Real-time Logger Class ──────────────────────────────
class StreamLogger:
    """Intercepts print() and sends text to a live queue instantly."""
    def __init__(self, queue, original_stdout):
        self.queue = queue
        self.original_stdout = original_stdout

    def write(self, text):
        if text.strip():  # Only queue actual text, skip empty spacing
            self.queue.put(text.strip())
        self.original_stdout.write(text)  # Keep printing to the actual terminal too

    def flush(self):
        self.original_stdout.flush()
# ─────────────────────────────────────────────────────────────

@router.get("/run")
def run_pipeline():
    def stream():
        if pipeline_status.get("running"):
            yield "data: [ERROR] Pipeline is already running.\n\n"
            return

        pipeline_status["running"] = True
        original_stdout = sys.stdout
        
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from agents.repricer_chain import run_repricer_chain 
            
            start_msg = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 PIPELINE STARTED"
            append_log(start_msg)
            yield f"data: {start_msg}\n\n"

            # 1. Create a queue and attach our interceptor
            log_queue = Queue()
            sys.stdout = StreamLogger(log_queue, original_stdout)

            # 2. Track background thread status
            task_state = {"is_done": False, "error": None}

            def background_task():
                try:
                    run_repricer_chain()
                except Exception as e:
                    task_state["error"] = str(e)
                finally:
                    task_state["is_done"] = True

            # 3. Start the scraping pipeline in a background thread
            worker_thread = threading.Thread(target=background_task)
            worker_thread.start()

            # 4. Read from the queue and stream to React INSTANTLY
            while not task_state["is_done"] or not log_queue.empty():
                try:
                    # Wait 0.5 seconds for new text
                    line = log_queue.get(timeout=0.5)
                    append_log(line)
                    yield f"data: {line}\n\n"
                except Empty:
                    # If no text arrived in 0.5s, send an invisible heartbeat!
                    # This guarantees the React browser NEVER times out.
                    yield ": heartbeat\n\n"

            # 5. Handle completion or errors
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
            # 6. CRITICAL: Always give sys.stdout back to Python!
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