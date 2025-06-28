import logging
import os
from datetime import datetime
import glob

LOG_DIR = "logs"
MAX_LOG_FILES = 10

def setup_logging(config):
    """
    Configures the logging system for the application.
    Creates a new log file with a timestamp, and cleans up old log files.
    """
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Generate timestamped log file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"app_log_{timestamp}.log")

    # Configure logger
    logger = logging.getLogger('plate_analyzer')
    logger.setLevel(logging.DEBUG) # Always capture all messages for the logger itself

    # Remove existing handlers to prevent duplicate logs
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create file handler which logs all messages (DEBUG and above)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Create console handler with specified log_level
    ch = logging.StreamHandler()
    log_level_str = getattr(config, 'log_level', 'INFO').upper()
    if log_level_str == 'ALL':
        log_level_str = 'DEBUG'
    log_level = getattr(logging, log_level_str, logging.INFO)
    ch.setLevel(log_level)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info(f"Logging started. Log file: {log_file}")

    # Clean up old log files
    clean_old_log_files()
    
    return logger

def clean_old_log_files():
    """
    Deletes log files older than the MAX_LOG_FILES limit.
    """
    log_files = sorted(glob.glob(os.path.join(LOG_DIR, "app_log_*.log")))
    if len(log_files) > MAX_LOG_FILES:
        for old_file in log_files[:-MAX_LOG_FILES]:
            os.remove(old_file)
            logging.getLogger('plate_analyzer').info(f"Deleted old log file: {old_file}")

# Example usage (for testing purposes, remove in final integration)
if __name__ == "__main__":
    logger = setup_logging()
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Simulate multiple runs to test cleanup
    # for _ in range(15):
    #     setup_logging()
    #     import time
    #     time.sleep(0.1)
