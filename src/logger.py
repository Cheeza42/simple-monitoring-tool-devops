import logging
import os

# Set log file path to logs/app.log relative to current file
log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log')
os.makedirs(os.path.dirname(log_path), exist_ok=True)

# Configure logging system
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Export logger for use elsewhere
logger = logging.getLogger(__name__)
