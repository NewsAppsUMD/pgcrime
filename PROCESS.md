# Project Development Process

This document outlines the development of the Prince George's County Crime Statistics Dashboard, from initial data collection through final deployment.

## Project Overview

The Prince George's County Crime Statistics Dashboard provides public access to daily crime statistics from Prince George's County, Maryland. The system automatically downloads official crime reports, extracts structured data, and presents it through an interactive web dashboard that emphasizes trends and comparative analysis.

## Phase 1: Data Collection and Parsing

### Initial Challenge

Prince George's County publishes daily crime reports as PDF documents at https://dailycrime.princegeorgescountymd.gov/. While these reports are publicly available, the PDF format makes systematic analysis difficult. The data needed to be extracted, structured, and stored in a machine-readable format.

### Technical Implementation

**PDF Download System**
- Built automated downloader using Python's `requests` library
- Implemented error handling for network failures and missing reports
- Added logging to track download success and failures

**PDF Parsing**
- Selected `pdfplumber` library for its reliable table extraction capabilities
- Developed parser to extract report date from PDF headers
- Implemented multi-page table extraction to capture all incidents
- Structured extracted data into JSON format with consistent schema

**Data Storage**
- Established file naming convention: `YYYYMMDD.json` (e.g., `20260211.json`)
- Created directory structure:
  - `data/json/` - Primary storage for structured crime data
  - `data/pdf/` - Archive of original PDF reports
  - `logs/` - System logs and error tracking

**Key Files**
- `download_crime_report.py` - Main download and parsing orchestrator
- `parse_crime_pdf.py` - PDF extraction logic
- `config.py` - Centralized configuration management

### Data Structure

Each JSON file contains:
- Report date
- Crime statistics by offense type
- 7-day totals and comparisons
- Year-to-date figures for current and previous year
- Percentage changes for trend analysis

## Phase 2: Automation

### GitHub Actions Workflow

**Daily Data Collection**
- Workflow: `.github/workflows/daily-crime-report.yml`
- Schedule: Daily at 9 AM Eastern Time
- Process:
  1. Download latest PDF from county website
  2. Parse PDF to extract crime data
  3. Generate JSON file
  4. Update manifest listing available files
  5. Commit new data to repository
  6. Trigger website deployment

**Benefits**
- Eliminates manual data collection
- Ensures consistent daily updates
- Maintains complete historical record
- Automatic error logging for monitoring

## Phase 3: Dashboard Development

### Requirements Analysis

The dashboard needed to:
- Emphasize trends over raw numbers
- Show both short-term (7-day) and long-term (year-to-date) patterns
- Enable comparison between current and previous periods
- Present percentage changes prominently
- Allow filtering by crime category
- Maintain accessibility and mobile responsiveness

### Design Decisions

**Visual Hierarchy**
- Percentage changes displayed larger and more prominently than raw numbers
- Color coding: green for decreases, red for increases
- Clear labeling to distinguish 7-day vs year-to-date comparisons

**User Interface**
- Single-page application for simplicity
- Summary cards for high-level overview
- Interactive charts for visual trend analysis
- Searchable table for detailed data exploration
- Date selector for historical comparison

**Branding**
- Official Prince George's County colors: blue (#003DA5) and gold (#FFB81C)
- Professional appearance appropriate for official crime statistics
- Clear data attribution and source citation

### Technical Stack

**Frontend**
- Pure HTML/CSS/JavaScript (no framework dependencies)
- Chart.js for data visualizations
- Responsive CSS Grid and Flexbox layouts
- Modern browser features (ES6+)

**Data Loading**
- Manifest-based file discovery for reliable static hosting
- Automatic date range detection (last 30 days)
- Asynchronous data fetching
- Graceful error handling and user feedback

### Key Features Implemented

**Summary Cards**
- Total crime statistics
- Violent crime breakdown
- Property crime totals
- Homicide tracking
- Each showing 7-day totals and year-to-date comparisons

**Charts**
- Year-to-date overall crime comparison
- High-profile offenses (murder, robbery, carjacking, shootings)
- Property crime breakdown (burglary, larceny, stolen vehicles)
- 7-day trend comparison
- Daily breakdown view

**Data Table**
- Filterable by category (All, Violent, Property, High-Profile)
- Shows current 7-day totals
- Displays year-to-date figures for both years
- Calculates and highlights percentage changes

## Phase 4: Iterative Refinement

### User Feedback Integration

**Percentage Emphasis**
- Initial version showed raw numbers primarily
- Updated to lead with percentages, raw numbers in smaller font
- Added percentage changes to all chart tooltips

**Color Scheme**
- Started with generic blue/green color palette
- Updated to official Prince George's County seal colors
- Applied consistently across all UI elements

**7-Day Comparison Clarity**
- Initial implementation confused year-to-date and week-over-week changes
- Separated calculations for `ytdPctChange` and `weekPctChange`
- Added explicit label: "(vs prev. 7 days)" for clarity
- Lightened highlight card background for better readability

**Duplicate Label Removal**
- Identified redundant "2026 YTD" labels appearing twice
- Cleaned up card layout to show labels only in headers
- Improved visual hierarchy and reduced clutter

**Attribution**
- Added footer with data source citation
- Included creator byline and institutional affiliation
- Linked to official county crime reports website

## Phase 5: Deployment

### GitHub Pages Configuration

**Directory Structure**
- Renamed `website/` to `docs/` following GitHub Pages convention
- Maintains compatibility with both Actions and branch-based deployment

**Deployment Workflow**
- Workflow: `.github/workflows/deploy-pages.yml`
- Triggers on changes to:
  - `docs/` directory (website code)
  - `data/json/` directory (new crime data)
  - Workflow file itself
- Can be manually triggered when needed

**Build Process**
1. Copy `docs/` directory contents
2. Copy `data/json/` files (symlinks don't work in GitHub Pages artifacts)
3. Upload artifact for Pages deployment
4. Deploy to production

### Deployment Challenges and Solutions

**Symlink Issue**
- Problem: GitHub Pages doesn't support symlinks in artifacts
- Solution: Changed from symlink creation to direct file copying
- Result: Data files properly accessible at deployment

**File Discovery**
- Problem: HTTP probing for files unreliable on static hosting
- Solution: Created `manifest.json` listing all available files
- Implementation: `update_manifest.py` script regenerates after each data update
- Result: Fast, reliable file discovery on initial page load

**Path Configuration**
- Local development: Uses `./data/json/` path with symlink
- Production deployment: Same path works with copied files
- Consistent behavior across environments

## Phase 6: Documentation

Created comprehensive documentation:
- `README.md` - Project overview and setup instructions
- `DEPLOYMENT.md` - Detailed deployment guide and troubleshooting
- `DEPLOYMENT-CHECKLIST.md` - Quick reference for deployment steps
- `docs/README.md` - Dashboard-specific documentation
- `CLAUDE.md` - Technical context for project maintenance
- `PROCESS.md` - This document

## Current State

### Automated Pipeline

1. Daily at 9 AM ET: GitHub Actions downloads latest crime report
2. PDF is parsed and converted to structured JSON
3. Manifest file is updated with new data
4. Changes are committed to repository
5. Website deployment is automatically triggered
6. Dashboard updates with latest statistics within minutes

### Live Dashboard

- URL: https://newsappsumd.github.io/pgcrime/
- Updates automatically when new data is available
- Presents last 30 days of crime statistics
- Provides year-to-date comparisons
- Shows percentage-based trend analysis

### Maintenance Requirements

**Minimal Ongoing Work**
- System runs automatically without intervention
- GitHub Actions handles all data collection and deployment
- Failures are logged for review if they occur

**Potential Manual Tasks**
- Monitoring workflow runs for failures
- Updating parser if PDF format changes
- Reviewing data quality and accuracy
- Adding new features or visualizations as needed

## Technical Decisions

### Why Python for Parsing?
- Excellent PDF processing libraries (`pdfplumber`)
- Strong data manipulation capabilities
- Easy integration with GitHub Actions
- Well-suited for scheduled automation

### Why No Backend/Database?
- Crime data is public information
- Historical data volume is manageable as static files
- Eliminates hosting costs and complexity
- JSON files are version-controlled for audit trail
- Simplifies deployment and maintenance

### Why Single-Page Application?
- Reduces complexity
- Fast performance (no page reloads)
- Works offline once loaded
- Easy to deploy anywhere
- Minimal dependencies

### Why Manifest File?
- Static hosting can't list directory contents
- More reliable than probing individual files
- Faster initial load (one request vs. many)
- Easy to regenerate automatically
- Enables quick feature detection

## Lessons Learned

**PDF Parsing Reliability**
- Different PDF generators produce different structures
- Test with multiple samples before finalizing parser
- Build flexibility into extraction logic
- Log parsing errors for debugging

**Static Hosting Constraints**
- Symlinks don't survive artifact upload
- Directory listing not available
- Need explicit file manifests
- CORS and path handling differ from local servers

**Automation Benefits**
- Initial setup time pays off quickly
- Reduces human error
- Ensures consistency
- Enables reliable daily updates
- Frees time for analysis rather than data collection

**User Interface Priorities**
- Percentage changes more meaningful than raw numbers for trends
- Consistent color coding aids understanding
- Clear labels prevent confusion
- Mobile responsiveness is essential for public access

## Future Enhancements

Potential improvements identified but not yet implemented:

**Data Analysis**
- Historical trend lines over months/years
- Seasonal pattern detection
- Geographic mapping (requires address geocoding)
- Statistical anomaly detection

**User Features**
- Custom date range selection
- Downloadable CSV reports
- Chart export as images
- Email/SMS notifications for significant changes

**Technical Improvements**
- Database storage for faster queries
- API for programmatic access
- Automated data quality checks
- Performance monitoring

**Visualization**
- Heat maps by time and location
- Crime type correlation analysis
- Comparative dashboards (multiple jurisdictions)
- Predictive modeling displays

## Conclusion

This project demonstrates the value of automating public data access. By converting daily PDF reports into structured, interactive visualizations, the dashboard makes Prince George's County crime statistics more accessible and understandable to the public, researchers, and policymakers.

The automated pipeline ensures the dashboard stays current without manual intervention, while the emphasis on percentage changes and trend analysis helps users quickly identify patterns and changes in crime statistics over time.
