# Quick Start Guide

## Getting Started in 30 Seconds

1. **Navigate to the website directory:**
   ```bash
   cd website
   ```

2. **Start the server:**
   ```bash
   ./serve.sh
   ```

   Or manually:
   ```bash
   python3 -m http.server 8000
   ```

3. **Open in your browser:**
   ```
   http://localhost:8000
   ```

That's it! The dashboard will automatically load the latest crime data.

## What You'll See

### Top Section - Summary Cards
- **Total Crime**: Overall incidents with 7-day totals and YTD comparisons
- **Violent Crime**: Assaults, robberies, homicides
- **Property Crime**: Burglaries, thefts, stolen vehicles
- **Homicides**: Murder statistics with trend indicators

### Visual Trend Charts
1. **YTD Comparison Charts**:
   - Overall crime (2026 vs 2025)
   - High-profile offenses (murder, robbery, carjacking, shootings)
   - Property crime breakdown

2. **7-Day Trends**:
   - Current week vs previous week
   - Daily breakdown line chart showing trends across 7 days

### Interactive Data Table
- Select different report dates from dropdown
- Filter by category (All, Violent, Property, High-Profile)
- Color-coded changes (green = decrease, red = increase)

## Understanding the Data

### Change Indicators
- **Green with ↓**: Crime decreased (good)
- **Red with ↑**: Crime increased (needs attention)
- **Gray**: No change

### YTD Comparisons
- Shows 2026 year-to-date vs same period in 2025
- Helps identify long-term trends
- Accounts for seasonal variations

### 7-Day Totals
- Most recent 7-day period
- Compared to previous 7 days
- Shows short-term trends and spikes

## Tips for Best Results

1. **Check the "Last Updated" date** at the top to see when data was last refreshed

2. **Use the category filter** to focus on specific crime types:
   - **Violent Crimes**: Personal safety concerns
   - **Property Crimes**: Theft and burglary
   - **High-Profile**: Most serious offenses

3. **Compare different dates** using the date selector to see how crime evolves

4. **Look for patterns**:
   - Are weekends higher than weekdays?
   - Are certain crime types increasing/decreasing?
   - How does this year compare to last year?

## Troubleshooting

### "Loading..." doesn't go away
- Make sure you're running the server from the `website` directory
- Check that `../data/json/` contains JSON files
- Look at browser console for errors (F12)

### No data showing
- Verify JSON files exist: `ls ../data/json/`
- Ensure files follow naming format: `YYYYMMDD.json`
- Check that files contain valid JSON

### Charts not rendering
- Ensure you have internet connection (Chart.js loads from CDN)
- Check browser console for JavaScript errors
- Try a different browser

## Advanced Usage

### Embedding in Another Site
Copy the entire `website` folder and ensure the data directory is accessible.

### Customizing Colors
Edit the CSS variables in `index.html` under the `:root` selector.

### Adding More Charts
Edit `app.js` and add new chart rendering methods following the existing patterns.

## Data Sources

Data comes from the Prince George's County Police Department daily crime reports, automatically parsed and converted to JSON format by the crime report parser tool.

## Support

For issues or questions, check the main README.md or repository documentation.
