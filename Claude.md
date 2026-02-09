# Claude Context: Prince George's County Crime Report Parser

## Project Purpose

This project automates downloading and parsing daily crime reports from Prince George's County, Maryland. The goal is to convert PDF reports into structured JSON data for analysis, with each day saved as a separate file.

## Key Requirements

1. **Daily Downloads**: Fetch PDF from https://dailycrime.princegeorgescountymd.gov/ once per day
2. **Structured Data**: Parse PDF into JSON format with CSV export option
3. **File Naming**: Each day's data saved as `yyyymmdd.json` (e.g., `20260209.json`)
4. **Date Extraction**: Extract the report date from the top of the PDF and include it in the JSON
5. **Technology**: Python with `pdfplumber` for PDF parsing

## Technical Stack

### Core Libraries
- **pdfplumber**: PDF text and table extraction (preferred for this project)
- **requests**: HTTP downloads
- **json**: JSON serialization
- **csv**: CSV export functionality
- **datetime/dateutil**: Date parsing and formatting
- **schedule** (optional): Automated scheduling
- **logging**: Error tracking and debugging

### Why pdfplumber?
- Excellent table extraction capabilities
- Better text positioning than PyPDF2
- Can handle complex PDF layouts
- Active development and good documentation

## Project Architecture

### Core Scripts

1. **download_crime_report.py**: Main entry point
   - Downloads PDF from URL
   - Calls parser
   - Saves JSON output
   - Handles errors and logging

2. **parse_crime_pdf.py**: PDF parsing logic
   - Opens PDF with pdfplumber
   - Extracts report date from header
   - Parses incident tables/text
   - Structures data into JSON format
   - Returns parsed data dictionary

3. **json_to_csv.py**: CSV conversion utility
   - Reads JSON files
   - Flattens nested structure
   - Exports to CSV

4. **config.py**: Configuration management
   - URLs, paths, settings
   - Centralized configuration

5. **scheduler.py** (optional): Automated scheduling
   - Runs download script daily
   - Uses `schedule` library or system cron

### Directory Structure

```
data/
  json/      - Primary output: yyyymmdd.json files
  csv/       - Optional CSV exports
  pdf/       - Archived PDF files (for reference)
logs/        - Application and error logs
```

## PDF Parsing Strategy

### Expected PDF Structure

Based on typical daily crime reports:
1. **Header**: Date, jurisdiction, report type
2. **Incident Table**: Rows of crime incidents with columns like:
   - Date/Time
   - Incident Type
   - Location/Address
   - District/Area
   - Case Number
   - Description/Notes

### Parsing Approach

```python
import pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    # Extract date from first page header
    first_page = pdf.pages[0]
    header_text = first_page.extract_text()[:200]  # Top portion
    report_date = extract_date(header_text)

    # Extract tables from all pages
    all_incidents = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            incidents = parse_incident_table(table)
            all_incidents.extend(incidents)
```

### Date Extraction

The PDF likely has a date in the header like:
- "Daily Crime Report - February 9, 2026"
- "Report Date: 02/09/2026"
- "Prince George's County Police Department - 2/9/26"

Use regex and `dateutil.parser` to flexibly extract dates:

```python
from dateutil import parser
import re

def extract_date(header_text):
    # Try common date patterns
    patterns = [
        r'(\w+ \d{1,2}, \d{4})',  # February 9, 2026
        r'(\d{1,2}/\d{1,2}/\d{4})',  # 02/09/2026
        r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
    ]

    for pattern in patterns:
        match = re.search(pattern, header_text)
        if match:
            date_str = match.group(1)
            return parser.parse(date_str).date()

    return None
```

## Common Tasks for Claude

### 1. Implementing the Parser

When asked to create the parser:
- Install pdfplumber: `pip install pdfplumber`
- Download a sample PDF first to examine structure
- Use pdfplumber's `.extract_tables()` for tabular data
- Use `.extract_text()` for header date extraction
- Handle multi-page PDFs
- Include robust error handling

### 2. Testing

```bash
# Download today's report manually
python download_crime_report.py --date 2026-02-09

# Parse a specific PDF
python parse_crime_pdf.py data/pdf/20260209.pdf --output data/json/20260209.json

# Test with debug output
python download_crime_report.py --debug
```

### 3. Debugging PDF Structure

```python
# Quick script to inspect PDF structure
import pdfplumber

with pdfplumber.open('sample.pdf') as pdf:
    page = pdf.pages[0]
    print("Text:", page.extract_text()[:500])
    print("\nTables:", len(page.extract_tables()))
    print("Table preview:", page.extract_tables()[0][:3])
```

### 4. Handling Edge Cases

- **No PDF available**: Some days may not have reports (holidays, weekends)
- **Format changes**: County may update PDF layout
- **Empty tables**: Some days may have no incidents
- **Multi-page tables**: Tables may span multiple pages
- **OCR PDFs**: If PDF is scanned image, pdfplumber can still extract text but may need OCR preprocessing

### 5. Adding Features

**Weekly/Monthly Summaries**:
```python
# Aggregate multiple JSON files
import json
import glob

def create_weekly_summary(start_date):
    # Load week's worth of JSON files
    # Aggregate statistics
    # Generate summary report
```

**Geolocation**:
```python
# Geocode addresses for mapping
from geopy.geocoders import Nominatim

def geocode_incidents(incidents):
    # Add lat/lon to each incident
    # Requires addresses in consistent format
```

**Visualization**:
```python
# Generate crime heatmap or charts
import matplotlib.pyplot as plt
import pandas as pd

def visualize_trends(json_files):
    # Load data, create charts
```

## Scheduling Options

### Option 1: Python `schedule` library
```python
import schedule
import time

schedule.every().day.at("06:00").do(download_and_parse)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Option 2: Cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add line:
0 6 * * * cd /path/to/pgcrime && /usr/bin/python3 download_crime_report.py >> logs/cron.log 2>&1
```

### Option 3: Windows Task Scheduler
Create scheduled task via GUI or PowerShell.

### Option 4: Docker with cron
For containerized deployment.

## Error Handling

Must handle:
1. **Network errors**: PDF download fails
2. **Parsing errors**: PDF structure changed
3. **Date extraction fails**: Header format changed
4. **File I/O errors**: Disk full, permission issues
5. **Invalid data**: Missing fields, malformed tables

All errors should:
- Log to `logs/crime_parser.log`
- Not crash the scheduler (catch exceptions)
- Optionally send notifications (email/SMS)

## Testing Strategy

1. **Unit tests**: Test individual parsing functions
2. **Integration tests**: Full download→parse→save workflow
3. **Sample PDFs**: Keep examples of different PDF formats
4. **Date range tests**: Verify file naming with different dates
5. **Edge cases**: Empty reports, holidays, format changes

## Future Enhancements

- Database storage (SQLite, PostgreSQL)
- Web dashboard for visualization
- Email notifications on errors
- Crime trend analysis
- Integration with mapping services
- API for querying historical data
- Machine learning for crime prediction
- Automatic format detection if PDF structure changes

## Maintenance Notes

### When PDF Format Changes

If the county updates their PDF format:
1. Download a sample of the new format
2. Use pdfplumber to inspect structure (see debugging section)
3. Update parsing logic in `parse_crime_pdf.py`
4. Test with multiple samples
5. Update this documentation

### When URL Changes

If the PDF URL changes:
1. Update `config.py` with new URL
2. Test download functionality
3. Document change in README.md changelog

## Security Considerations

- PDFs are from trusted government source (Prince George's County)
- No sensitive credentials needed
- Data is public record
- Consider rate limiting to avoid overwhelming county server
- Validate downloaded files are actual PDFs before parsing

## Performance

- PDFs are typically small (<5MB)
- Parsing takes 1-10 seconds per PDF
- JSON files are compact (<100KB typically)
- Can process years of data in minutes

## Questions Claude Should Ask User

When implementing or debugging:

1. **PDF Structure Unknown**: "I need to see a sample PDF to understand its structure. Can you download one manually so I can examine it?"

2. **Scheduling Preference**: "What's your preferred scheduling method: Python script, cron job, or Windows Task Scheduler?"

3. **Data Storage**: "Do you want to keep the downloaded PDFs archived, or delete them after parsing?"

4. **Notifications**: "Should the script notify you on errors (email/log only)?"

5. **CSV Format**: "For CSV export, do you want one file per day or one combined file?"

6. **Geocoding**: "Do you want address geocoding for mapping, or just text addresses?"

## Working with This Project

When user asks Claude to work on this project:

1. **Read README.md and Claude.md first** (you're doing this now!)
2. **Check if scripts exist** - they may not be created yet
3. **Examine a sample PDF** - critical for understanding structure
4. **Start with core functionality** - download and parse before scheduling
5. **Test incrementally** - don't build everything at once
6. **Update documentation** - keep README.md and this file current

## Quick Start for Claude

User says: "Implement the crime parser"

Your approach:
1. Acknowledge requirements
2. Check if pdfplumber is installed: `pip list | grep pdfplumber`
3. Try to download a sample PDF to examine structure
4. Create `parse_crime_pdf.py` with pdfplumber logic
5. Create `download_crime_report.py` as main script
6. Create `config.py` for settings
7. Create `requirements.txt`
8. Test with sample PDF
9. Create `json_to_csv.py` for CSV export
10. Document any findings or issues

## Resources

- pdfplumber docs: https://github.com/jsvine/pdfplumber
- Python requests: https://docs.python-requests.org/
- Prince George's County: https://dailycrime.princegeorgescountymd.gov/
- Schedule library: https://schedule.readthedocs.io/

## Contact & Context

- User prefers Python
- User specifically requested pdfplumber
- JSON is primary output, CSV is optional
- Date in filename must be yyyymmdd format
- Report date from PDF must be included in JSON

This file should be updated as the project evolves or requirements change.
