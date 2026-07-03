import sys
import os
import io
from contextlib import redirect_stdout
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.repricer_chain import run_repricer_chain
# Import our new logger function
from api.routers.pipeline import pipeline_status, append_log

scheduler = BackgroundScheduler()

def automated_pipeline_run():
    if pipeline_status.get("running"):
        append_log(f"[{datetime.now().strftime('%H:%M:%S')}] ⏩ Skipping scheduled run: Pipeline already active.")
        return

    append_log(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏰ AUTOMATED SCHEDULED RUN STARTED")
    pipeline_status["running"] = True
    
    try:
        # Capture the terminal output just like the manual run does
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            run_repricer_chain()
            
        # Write every line to the log file
        for line in buffer.getvalue().splitlines():
            append_log(line)

        pipeline_status["last_run"] = datetime.now().isoformat()
        append_log("✅ Background cycle complete.\n")
        
    except Exception as e:
        append_log(f"❌ Background cycle failed: {str(e)}\n")
    finally:
        pipeline_status["running"] = False

def start_scheduler():
    # You can change hours=6 to minutes=1 to test it quickly!
    scheduler.add_job(automated_pipeline_run, 'interval', hours = 6, id='auto_repricer')
    scheduler.start()
    print("⏰ Background scheduler activated!")

def stop_scheduler():
    scheduler.shutdown()