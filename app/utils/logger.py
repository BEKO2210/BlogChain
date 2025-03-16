import os
import logging
import logging.handlers
from datetime import datetime
import json
from colorlog import ColoredFormatter
import base64
import hashlib
import sys

# Configuration
LOG_LEVEL = logging.INFO
LOG_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 30  # Keep up to 30 backup logs

# Color format for console output
COLOR_FORMAT = '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Ensure log directory exists
os.makedirs(LOG_DIRECTORY, exist_ok=True)

# Keep track of loggers to avoid creating duplicates
LOGGERS = {}

def encrypt_log_file(log_file, encryption_key):
    """
    Encrypt a log file using the provided encryption key.
    Uses a simple symmetric encryption method.
    
    Args:
        log_file (str): Path to the log file
        encryption_key (bytes or str): Key to encrypt the file
    """
    if not os.path.exists(log_file):
        return
    
    if isinstance(encryption_key, str):
        encryption_key = encryption_key.encode()
    
    # Create a hash of the key
    key_hash = hashlib.sha256(encryption_key).digest()
    
    try:
        with open(log_file, 'rb') as f:
            content = f.read()
        
        # Simple XOR encryption
        encrypted = bytearray()
        for i, byte in enumerate(content):
            encrypted.append(byte ^ key_hash[i % len(key_hash)])
        
        with open(log_file + '.encrypted', 'wb') as f:
            f.write(encrypted)
        
        # Remove the original file
        os.remove(log_file)
        
        return True
    except Exception as e:
        print(f"Error encrypting log file: {str(e)}")
        return False

def decrypt_log_file(encrypted_file, encryption_key):
    """
    Decrypt a log file that was encrypted with encrypt_log_file.
    
    Args:
        encrypted_file (str): Path to the encrypted log file
        encryption_key (bytes or str): Key to decrypt the file
        
    Returns:
        str: Decrypted content as string
    """
    if not os.path.exists(encrypted_file):
        return None
    
    if isinstance(encryption_key, str):
        encryption_key = encryption_key.encode()
    
    # Create a hash of the key
    key_hash = hashlib.sha256(encryption_key).digest()
    
    try:
        with open(encrypted_file, 'rb') as f:
            content = f.read()
        
        # Simple XOR decryption (same as encryption)
        decrypted = bytearray()
        for i, byte in enumerate(content):
            decrypted.append(byte ^ key_hash[i % len(key_hash)])
        
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Error decrypting log file: {str(e)}")
        return None

class SecureRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Custom rotating file handler that encrypts log files when they are rotated.
    """
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, 
                 encoding=None, delay=False, encryption_key=None):
        self.encryption_key = encryption_key
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
    
    def doRollover(self):
        """
        Override doRollover to encrypt the rotated file.
        """
        super().doRollover()
        
        # Get the file that was just rotated
        rotated_file = f"{self.baseFilename}.1"
        
        # Encrypt if we have an encryption key
        if self.encryption_key and os.path.exists(rotated_file):
            encrypt_log_file(rotated_file, self.encryption_key)

class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON objects for better structured logging.
    """
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).strftime(LOG_DATE_FORMAT),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        
        # Include exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def get_file_handler(name, encryption_key=None, level=LOG_LEVEL, log_format=LOG_FORMAT):
    """
    Create a file handler with rotation and optional encryption.
    
    Args:
        name (str): Name for the log file
        encryption_key (bytes, optional): Key for encrypting rotated logs
        level: Logging level
        log_format: Format string for logs
        
    Returns:
        logging.Handler: Configured file handler
    """
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(LOG_DIRECTORY, f"{name}_{today}.log")
    
    if encryption_key:
        handler = SecureRotatingFileHandler(
            log_file, 
            maxBytes=LOG_MAX_BYTES, 
            backupCount=LOG_BACKUP_COUNT,
            encryption_key=encryption_key
        )
    else:
        handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=LOG_MAX_BYTES, 
            backupCount=LOG_BACKUP_COUNT
        )
    
    formatter = logging.Formatter(log_format, LOG_DATE_FORMAT)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler

def get_console_handler(level=LOG_LEVEL):
    """
    Create a console handler with colored output.
    
    Args:
        level: Logging level
        
    Returns:
        logging.Handler: Configured console handler
    """
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        COLOR_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler

def get_json_file_handler(name, encryption_key=None, level=LOG_LEVEL):
    """
    Create a file handler that writes logs in JSON format.
    
    Args:
        name (str): Name for the log file
        encryption_key (bytes, optional): Key for encrypting rotated logs
        level: Logging level
        
    Returns:
        logging.Handler: Configured JSON file handler
    """
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(LOG_DIRECTORY, f"{name}_{today}_json.log")
    
    if encryption_key:
        handler = SecureRotatingFileHandler(
            log_file, 
            maxBytes=LOG_MAX_BYTES, 
            backupCount=LOG_BACKUP_COUNT,
            encryption_key=encryption_key
        )
    else:
        handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=LOG_MAX_BYTES, 
            backupCount=LOG_BACKUP_COUNT
        )
    
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler

def get_logger(name, encryption_key=None, level=LOG_LEVEL, include_json=False):
    """
    Get a logger with the specified name and configuration.
    
    Args:
        name (str): Logger name (usually __name__)
        encryption_key (bytes, optional): Key for encrypting rotated logs
        level: Logging level
        include_json (bool): Whether to include a JSON formatted log file
        
    Returns:
        logging.Logger: Configured logger
    """
    # Check if we already have this logger
    if name in LOGGERS:
        return LOGGERS[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add handlers
    logger.addHandler(get_file_handler(name, encryption_key, level))
    logger.addHandler(get_console_handler(level))
    
    if include_json:
        logger.addHandler(get_json_file_handler(name, encryption_key, level))
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Store in cache
    LOGGERS[name] = logger
    
    return logger

def set_log_level(level):
    """
    Set the logging level for all handlers of all loggers.
    
    Args:
        level: New logging level
    """
    for logger_name, logger in LOGGERS.items():
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)

def add_user_context(logger, user_id):
    """
    Add a filter to include user_id in all log records.
    
    Args:
        logger (logging.Logger): Logger to add context to
        user_id (str): User ID to include in logs
    """
    class UserContextFilter(logging.Filter):
        def filter(self, record):
            record.user_id = user_id
            return True
    
    # Remove any existing user context filters
    for filter in logger.filters[:]:
        if isinstance(filter, UserContextFilter):
            logger.removeFilter(filter)
    
    # Add the new filter
    logger.addFilter(UserContextFilter())

# Initialize a default logger for the application
app_logger = get_logger('blockjournal')
