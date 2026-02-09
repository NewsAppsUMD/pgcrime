# Prince George's County Daily Crime Report Parser

Automated tool to download and parse daily crime reports from Prince George's County, Maryland into structured JSON/CSV data.

## Overview

This project downloads PDF crime reports from https://dailycrime.princegeorgescountymd.gov/ on a daily schedule, extracts structured data, and saves it in JSON format with optional CSV export. Each day's report is stored as a separate file named `yyyymmdd.json`.

## Features

- **Automated Daily Downloads**: Scheduled to run once per day
- **PDF Parsing**: Uses `pdfplumber` to extract text and tables from PDF reports
- **Structured Output**: Generates clean JSON files with crime incident data
- **CSV Export Option**: Convert JSON data to CSV format for analysis
- **Date Tracking**: Extracts and includes the report date from the PDF header
- **Error Handling**: Robust error handling for network issues and parsing failures

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `pdfplumber` - PDF parsing
- `requests` - HTTP requests for downloading PDFs
- `python-dateutil` - Date parsing
- `schedule` (optional) - For automated scheduling

## Project Structure

```
pgcrime/
├── README.md                  # This file
├── Claude.md                  # Context file for Claude AI assistant
├── requirements.txt           # Python dependencies
├── download_crime_report.py   # Main script
├── parse_crime_pdf.py         # PDF parsing logic
├── config.py                  # Configuration settings
├── data/                      # Output directory
│   ├── json/                  # JSON files (yyyymmdd.json)
│   ├── csv/                   # CSV exports (optional)
│   └── pdf/                   # Downloaded PDFs (archived)
└── logs/                      # Application logs

```

## Usage

### Manual Execution

Download and parse today's report:
```bash
python download_crime_report.py
```

### Scheduled Execution

Run the scheduler (executes daily at configured time):
```bash
python scheduler.py
```

Or use system cron (Linux/Mac):
```bash
# Add to crontab (runs daily at 6 AM)
0 6 * * * cd /path/to/pgcrime && python download_crime_report.py
```

Windows Task Scheduler:
```powershell
# Create a daily task
schtasks /create /tn "PGCrimeDailyDownload" /tr "python C:\path\to\pgcrime\download_crime_report.py" /sc daily /st 06:00
```

### CSV Export

Convert JSON to CSV:
```bash
python json_to_csv.py data/json/20260209.json
```

Convert all JSON files to CSV:
```bash
python json_to_csv.py --all
```

## Output Format

### JSON Structure

```json
{
  "report_date": "2026-02-09",
  "extracted_date": "February 9, 2026",
  "download_timestamp": "2026-02-09T10:30:00Z",
  "source_url": "https://dailycrime.princegeorgescountymd.gov/",
  "incidents": [
    {
      "incident_type": "Robbery",
      "date": "2026-02-08",
      "time": "14:30",
      "location": "1234 Main St, Hyattsville",
      "district": "District 1",
      "description": "Armed robbery at convenience store",
      "case_number": "2026-000123"
    }
  ],
  "summary": {
    "total_incidents": 15,
    "by_type": {
      "Robbery": 2,
      "Assault": 5,
      "Burglary": 8
    }
  }
}
```

### CSV Format

Flattened incident data with one row per incident.

## Configuration

Edit `config.py` to customize:

```python
# PDF source URL
PDF_URL = "https://dailycrime.princegeorgescountymd.gov/"

# Output directories
JSON_OUTPUT_DIR = "data/json"
CSV_OUTPUT_DIR = "data/csv"
PDF_ARCHIVE_DIR = "data/pdf"

# Scheduling (if using scheduler.py)
DAILY_RUN_TIME = "06:00"  # 6 AM daily

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/crime_parser.log"
```

## Troubleshooting

### PDF Download Fails
- Check internet connection
- Verify the URL is accessible: https://dailycrime.princegeorgescountymd.gov/
- Check if the county website structure has changed

### Parsing Errors
- Verify PDF format hasn't changed (county may update layout)
- Check logs for specific error messages
- Run with `--debug` flag for verbose output

### Missing Data
- PDF may not be available for certain dates (weekends/holidays)
- Check if the PDF structure differs on certain days

## Data Analysis

Example Python code to analyze collected data:

```python
import json
import glob
from collections import Counter

# Load all JSON files
incidents = []
for file in glob.glob("data/json/*.json"):
    with open(file) as f:
        data = json.load(f)
        incidents.extend(data["incidents"])

# Analyze crime types
crime_types = Counter(i["incident_type"] for i in incidents)
print(f"Most common crimes: {crime_types.most_common(5)}")
```

## Contributing

When making changes:
1. Test with recent PDFs to ensure parsing works
2. Update `Claude.md` if project structure changes
3. Add error handling for edge cases
4. Document any new configuration options

## License

This project is for personal/research use. Crime data is public record from Prince George's County.

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review `Claude.md` for technical context
- Verify PDF structure hasn't changed on county website

## Changelog

### Version 1.0.0 (Initial)
- Initial project setup
- PDF download and parsing with pdfplumber
- JSON output with daily files
- CSV export option
- Scheduled execution support
