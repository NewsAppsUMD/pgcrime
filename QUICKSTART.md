# Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### 1. Parse a Local PDF

```bash
# Parse the PDF you already have
python parse_crime_pdf.py DailyCrime.pdf > data/json/20260208.json
```

### 2. Download and Parse from URL

```bash
# Download today's report and parse it
python download_crime_report.py
```

### 3. Convert JSON to CSV

```bash
# Convert a single JSON file
python json_to_csv.py data/json/20260208.json

# Convert all JSON files
python json_to_csv.py --all

# Create one combined CSV from all JSON files
python json_to_csv.py --combined
```

### 4. Set Up Daily Automation

**Option A: Python Scheduler (runs continuously)**
```bash
python scheduler.py
```

**Option B: Cron Job (Linux/Mac)**
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6 AM
0 6 * * * cd /path/to/pgcrime && python download_crime_report.py
```

**Option C: Windows Task Scheduler**
```powershell
# Run as Administrator
schtasks /create /tn "PGCrimeDaily" /tr "python C:\path\to\pgcrime\download_crime_report.py" /sc daily /st 06:00
```

## Output Files

After running the scripts, you'll have:

- `data/json/YYYYMMDD.json` - Structured crime data
- `data/csv/YYYYMMDD.csv` - CSV export (if converted)
- `data/pdf/YYYYMMDD.pdf` - Archived PDF
- `logs/crime_parser.log` - Application logs

## Example JSON Structure

```json
{
  "report_date": "2026-02-08",
  "extracted_date_text": "Sunday, February 8, 2026",
  "crime_statistics": [
    {
      "offense_type": "Murder",
      "Monday 2/2": 0,
      "Tuesday 2/3": 1,
      "7-Day Totals": 2,
      "YTD 26 1/1-2/8": 9
    }
  ],
  "summary": {
    "violent_crime_count": 15,
    "property_crime_count": 15
  }
}
```

## Testing

```bash
# Test parsing with debug output
python parse_crime_pdf.py DailyCrime.pdf

# Test download with debug mode
python download_crime_report.py --debug

# Test CSV conversion
python json_to_csv.py data/json/20260208.json --output test.csv
```

## Troubleshooting

**Q: PDF download fails with 403 error?**
- The URL may require a browser session or may block automated requests
- Try manually downloading the PDF and using `parse_crime_pdf.py` directly

**Q: Date extraction fails?**
- Check if the PDF format has changed
- Update `DATE_PATTERNS` in `config.py`

**Q: Table parsing is incorrect?**
- Examine the PDF structure with: `python parse_crime_pdf.py --debug`
- The county may have changed their report format

## Next Steps

1. Set up automated daily downloads (scheduler or cron)
2. Configure `config.py` for your preferences
3. Consider adding notifications for errors
4. Build analysis tools using the JSON/CSV data

See `README.md` for full documentation.
