import logging
import os
from datetime import datetime
import glob

LOG_DIR = "logs"
MAX_LOG_FILES = 10

_LOGGER_INSTANCE = None
_LOG_FILE_HANDLER = None
_CONSOLE_HANDLER = None
_LOG_FILE_PATH = None


def setup_logging(config):
    """
    Configura (o actualiza) el sistema de logging de la aplicación.
    - Solo crea un archivo de log por ejecución.
    - Cambiar el nivel de log solo actualiza los handlers existentes.
    - Si ya existe logger, solo actualiza los niveles.
    Args:
        config: objeto de configuración con el atributo log_level.
    Returns:
        logging.Logger
    """
    global _LOGGER_INSTANCE, _LOG_FILE_HANDLER, _CONSOLE_HANDLER, _LOG_FILE_PATH
    logger = logging.getLogger('plate_analyzer')
    logger.propagate = False
    if _LOGGER_INSTANCE is not None:
        # Solo actualizar niveles
        log_level_str = getattr(config, 'log_level', 'INFO').upper()
        if log_level_str == 'ALL':
            log_level_str = 'DEBUG'
        log_level = getattr(logging, log_level_str, logging.INFO)
        if _CONSOLE_HANDLER:
            _CONSOLE_HANDLER.setLevel(log_level)
        logger.info(f"Log level updated to: {log_level_str}")
        return logger

    # Primera vez: crear archivo y handlers
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"app_log_{timestamp}.log")
    _LOG_FILE_PATH = log_file

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    # Console handler
    ch = logging.StreamHandler()
    log_level_str = getattr(config, 'log_level', 'INFO').upper()
    if log_level_str == 'ALL':
        log_level_str = 'DEBUG'
    log_level = getattr(logging, log_level_str, logging.INFO)
    ch.setLevel(log_level)
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # Remove existing handlers (if any, for safety)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # Add handlers
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
    logger.info(f"Logging started. Log file: {log_file}")
    # Clean old logs
    clean_old_log_files()
    # Save global references
    _LOGGER_INSTANCE = logger
    _LOG_FILE_HANDLER = fh
    _CONSOLE_HANDLER = ch
    return logger

def clean_old_log_files():
    """
    Elimina archivos de log antiguos si se supera el límite MAX_LOG_FILES.
    """
    log_files = sorted(glob.glob(os.path.join(LOG_DIR, "app_log_*.log")))
    if len(log_files) > MAX_LOG_FILES:
        for old_file in log_files[:-MAX_LOG_FILES]:
            try:
                os.remove(old_file)
                logging.getLogger('plate_analyzer').info(f"Deleted old log file: {old_file}")
            except Exception as e:
                logging.getLogger('plate_analyzer').warning(f"Could not delete old log file {old_file}: {e}")

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
