import logging
import sys

def setup_logging(log_level: int = logging.INFO):
    """
    Configures the root logger for the application.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    # Create a stream handler to output to console
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    
    # Create a formatter
    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    
    # Add the handler to the root logger
    root_logger.addHandler(stream_handler)

    # Configure specific loggers if needed
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)

    logging.info(f"Logging configured with level {logging.getLevelName(log_level)}")

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception 