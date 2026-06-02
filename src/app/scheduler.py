import time
import datetime
import threading
import logging
from typing import Callable

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DailyScheduler:
    """A lightweight, stateful background daemon thread scheduler that triggers a job daily at 10:00 AM local time."""
    def __init__(self, job_func: Callable[[], None]):
        self.job_func = job_func
        self.thread = None
        self.running = False
        
    def start(self):
        """Start the background scheduler thread."""
        if self.running:
            logger.warning("DailyScheduler is already running.")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True, name="DailySchedulerThread")
        self.thread.start()
        logger.info("DailyScheduler background daemon thread started successfully.")
        
    def stop(self):
        """Stop the background scheduler thread."""
        if not self.running:
            logger.warning("DailyScheduler is not running.")
            return
            
        self.running = False
        logger.info("DailyScheduler shutdown requested.")
        
    def _run_loop(self):
        """Execution loop calculating next execution interval and handling sleep."""
        while self.running:
            # 1. Calculate time remaining until next 10:00 AM local time
            now = datetime.datetime.now()
            target_today = now.replace(hour=10, minute=0, second=0, microsecond=0)
            
            if now < target_today:
                next_run = target_today
            else:
                next_run = target_today + datetime.timedelta(days=1)
                
            seconds_to_wait = (next_run - now).total_seconds()
            logger.info(f"DailyScheduler: Next re-indexing scheduled at 10:00 AM. Sleeping for {seconds_to_wait:.1f} seconds (~{seconds_to_wait / 3600:.2f} hours).")
            
            # Sleep in intervals of 60 seconds to allow for rapid thread shutdown/interruption
            sleep_interval = 60.0
            while seconds_to_wait > 0 and self.running:
                wait_time = min(seconds_to_wait, sleep_interval)
                time.sleep(wait_time)
                seconds_to_wait -= wait_time
                
            # 2. Trigger the job
            if self.running:
                logger.info("DailyScheduler: 10:00 AM local time reached. Triggering ingestion pipeline re-index...")
                try:
                    self.job_func()
                except Exception as e:
                    logger.error(f"DailyScheduler: Error encountered during background job execution: {e}")
                    
        logger.info("DailyScheduler thread terminated.")

# Simple self-testing execution block
if __name__ == "__main__":
    def test_job():
        logger.info("Scheduler test job executed!")
        
    logger.info("Starting scheduler test...")
    scheduler = DailyScheduler(test_job)
    scheduler.start()
    
    # Let it sleep for 3 seconds, then stop
    time.sleep(3)
    scheduler.stop()
    logger.info("Scheduler test completed.")
