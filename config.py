"""
Configuration settings for Prince George's County Crime Report Parser
"""

import os
from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).parent

# PDF source URL
PDF_URL = "https://dailycrime.princegeorgescountymd.gov/"

# Output directories
DATA_DIR = BASE_DIR / "data"
JSON_OUTPUT_DIR = DATA_DIR / "json"
CSV_OUTPUT_DIR = DATA_DIR / "csv"
PDF_ARCHIVE_DIR = DATA_DIR / "pdf"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [JSON_OUTPUT_DIR, CSV_OUTPUT_DIR, PDF_ARCHIVE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Scheduling (if using scheduler.py)
DAILY_RUN_TIME = "06:00"  # 6 AM daily

# Retry settings for downloads
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds
REQUEST_TIMEOUT = 30  # seconds

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = LOGS_DIR / "crime_parser.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# PDF parsing settings
# Date extraction patterns (regex)
DATE_PATTERNS = [
    r"(\w+,\s+\w+\s+\d{1,2},\s+\d{4})",  # Sunday, February 8, 2026
    r"(\w+\s+\d{1,2},\s+\d{4})",  # February 8, 2026
    r"(\d{1,2}/\d{1,2}/\d{4})",  # 02/08/2026
    r"Date:\s*(\d{1,2}/\d{1,2}/\d{4})",
]

# Table parsing settings
SKIP_EMPTY_ROWS = True
STRIP_WHITESPACE = True

# HTTP request headers (for automated downloads)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# Additional headers to mimic browser requests
REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

# Timezone
TIMEZONE = "America/New_York"
