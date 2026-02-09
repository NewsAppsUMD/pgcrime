"""
Scheduler for automated daily downloads of crime reports

This script runs continuously and executes the download script at a
scheduled time each day.
"""

import logging
import sys
import time
from datetime import datetime

import schedule

from config import DAILY_RUN_TIME, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT
from download_crime_report import main as download_main

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def scheduled_job():
    """Job to be executed on schedule."""
    logger.info("="*80)
    logger.info(f"Scheduled job triggered at {datetime.now()}")
    logger.info("="*80)

    try:
        result = download_main()
        if result == 0:
            logger.info("Scheduled job completed successfully")
        else:
            logger.error(f"Scheduled job failed with exit code {result}")
    except Exception as e:
        logger.error(f"Scheduled job encountered an error: {e}", exc_info=True)


def main():
    """Main scheduler loop."""
    logger.info("="*80)
    logger.info("Prince George's County Crime Report Scheduler Starting")
    logger.info("="*80)
    logger.info(f"Scheduled to run daily at: {DAILY_RUN_TIME}")
    logger.info(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*80)

    # Schedule the job
    schedule.every().day.at(DAILY_RUN_TIME).do(scheduled_job)

    # Optional: Run immediately on startup (comment out if not desired)
    # logger.info("Running initial job immediately...")
    # scheduled_job()

    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Scheduler encountered an error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
