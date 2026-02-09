# Daily Workflow Guide

## ⚠️ Important: Download Method

The URL https://dailycrime.princegeorgescountymd.gov/ may be blocked by proxy/firewall restrictions in certain environments.

### Recommended Workflow (Works Everywhere)

**Option 1: Manual Download + Parse (Recommended)**

This is the most reliable method:

```bash
# 1. Open browser and download PDF from:
#    https://dailycrime.princegeorgescountymd.gov/
#
# 2. Save to this folder as DailyCrime.pdf (or any name)
#
# 3. Parse it:
python parse_crime_pdf.py DailyCrime.pdf > data/json/$(date +%Y%m%d).json

# 4. Optional: Convert to CSV
python json_to_csv.py data/json/$(date +%Y%m%d).json
```

**Option 2: Automated Download (Requires No Proxy Restrictions)**

If running on your own server/machine without proxy restrictions:

```bash
# This attempts to download automatically
python download_crime_report.py
```

**Testing Download Capability:**

```bash
# Test if you can download
curl -I https://dailycrime.princegeorgescountymd.gov/

# If you see "403" or "blocked-by-allowlist", use manual workflow
```

## Daily Process

### Quick Daily Routine (5 minutes)

1. **Morning**: Visit https://dailycrime.princegeorgescountymd.gov/
2. **Save**: Download PDF to this folder
3. **Parse**: Run `python parse_crime_pdf.py <filename>.pdf > data/json/$(date +%Y%m%d).json`
4. **Done**: JSON file created with today's date

### Weekly Batch Process

If you download multiple days at once:

```bash
# Parse multiple PDFs
python parse_crime_pdf.py file1.pdf > data/json/20260208.json
python parse_crime_pdf.py file2.pdf > data/json/20260209.json

# Convert all to CSV
python json_to_csv.py --all

# Create combined CSV
python json_to_csv.py --combined
```

## Automation Options

### If You Can Download Automatically

**Option A: Cron (Linux/Mac)**
```bash
# Edit crontab
crontab -e

# Add daily job at 6 AM
0 6 * * * cd /path/to/pgcrime && python download_crime_report.py
```

**Option B: Windows Task Scheduler**
```powershell
schtasks /create /tn "PGCrimeDaily" /tr "python C:\path\to\pgcrime\download_crime_report.py" /sc daily /st 06:00
```

**Option C: Python Scheduler**
```bash
# Runs continuously, executes at scheduled time
python scheduler.py
```

### If Manual Download Required

**Option D: Semi-Automated Parser**

Create a simple script to parse any new PDFs in the folder:

```bash
#!/bin/bash
# parse_new_pdfs.sh

for pdf in *.pdf; do
    basename="${pdf%.pdf}"
    date_from_filename=$(echo $basename | grep -oE '[0-9]{8}')

    if [ -n "$date_from_filename" ]; then
        python parse_crime_pdf.py "$pdf" > "data/json/${date_from_filename}.json"
        echo "Parsed $pdf"
    fi
done
```

Save this as `parse_new_pdfs.sh`, make it executable (`chmod +x parse_new_pdfs.sh`), and run whenever you download new PDFs.

## Data Analysis Examples

### Quick Stats
```bash
# Count total crime types per day
cat data/json/20260208.json | python -m json.tool | grep offense_type | wc -l

# View summary
cat data/json/20260208.json | python -c "import sys,json; d=json.load(sys.stdin); print(f\"Date: {d['report_date']}\nViolent: {d['summary']['violent_crime_count']}\nProperty: {d['summary']['property_crime_count']}\")"
```

### Python Analysis
```python
import json
import glob

# Load all reports
reports = []
for file in glob.glob('data/json/*.json'):
    with open(file) as f:
        reports.append(json.load(f))

# Analyze trends
print(f"Total reports: {len(reports)}")
for report in reports:
    print(f"{report['report_date']}: {len(report['crime_statistics'])} offense types")
```

## Troubleshooting

**Q: Can't download PDF automatically?**
- Check: `curl -I https://dailycrime.princegeorgescountymd.gov/`
- If blocked: Use manual download workflow
- If not blocked: Update `config.py` with better headers

**Q: Parse errors?**
- Run with: `python parse_crime_pdf.py file.pdf` to see errors
- Check if PDF format changed
- View logs in `logs/crime_parser.log`

**Q: Wrong date extracted?**
- Check PDF header format
- Update `DATE_PATTERNS` in `config.py`

## Summary

**Best Practice**:
1. Manually download PDF daily from browser ✓
2. Save to this folder ✓
3. Run parser script ✓
4. Analyze JSON/CSV data ✓

This workflow is reliable, works everywhere, and takes just a few minutes per day.
