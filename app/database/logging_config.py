import logging
import sys
from pathlib import Path

# ANSI color codes
class Colors:
    DEBUG = '\033[36m'      # Cyan
    INFO = '\033[32m'       # Green
    WARNING = '\033[33m'    # Yellow
    ERROR = '\033[31m'      # Red
    CRITICAL = '\033[35m'   # Magenta
    RESET = '\033[0m'       # Reset

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    COLORS = {
        'DEBUG': Colors.DEBUG,
        'INFO': Colors.INFO,
        'WARNING': Colors.WARNING,
        'ERROR': Colors.ERROR,
        'CRITICAL': Colors.CRITICAL,
    }
    
    def format(self, record):
        # Get the original format
        log_color = self.COLORS.get(record.levelname, Colors.RESET)
        
        # Format: [LOG_LEVEL] filename:line : message
        filename = Path(record.pathname).name
        formatted_message = f"{log_color}[{record.levelname}]{Colors.RESET} {filename}:{record.lineno} : {record.getMessage()}"
        
        return formatted_message

def setup_database_logging(level=logging.INFO, log_file=None):
    """Setup colored logging for database operations"""
    
    # Create logger specifically for database operations
    logger = logging.getLogger('database')
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        # File handler uses plain format without colors
        file_formatter = logging.Formatter('[%(levelname)s] %(filename)s:%(lineno)d : %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Configure SQLAlchemy logging
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.WARNING)  # Only show warnings and errors
    sqlalchemy_logger.addHandler(console_handler)
    
    if log_file:
        sqlalchemy_logger.addHandler(file_handler)
    
    return logger

def get_database_logger():
    """Get the database logger instance"""
    return logging.getLogger('database')