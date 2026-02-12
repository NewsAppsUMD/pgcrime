# Website Files Overview

## Quick Start Files

### 🚀 QUICKSTART.md
- **Purpose**: Get the website running in 30 seconds
- **Use**: Follow this first if you want to see the dashboard immediately
- **Path**: `website/QUICKSTART.md`

### ▶️ serve.sh
- **Purpose**: Launch local development server
- **Usage**: `./serve.sh` from website directory
- **What it does**: Starts Python HTTP server on port 8000

### 🧪 test.html
- **Purpose**: Validate that data files are accessible
- **Usage**: Open in browser after starting server
- **What it tests**: 
  - Data file availability
  - JSON structure validation
  - Browser compatibility
  - Required features

## Main Application Files

### 📄 index.html
- **Purpose**: Main dashboard interface
- **Features**:
  - Summary cards for key metrics
  - Interactive charts (YTD comparisons, 7-day trends)
  - Data table with filtering
  - Responsive design

### ⚙️ app.js
- **Purpose**: Dashboard logic and data visualization
- **Key Classes**: `CrimeDashboard`
- **Features**:
  - Data loading and parsing
  - Chart rendering (Chart.js)
  - Table filtering and formatting
  - Event handling

## Documentation Files

### 📖 README.md
- **Purpose**: Comprehensive documentation
- **Covers**:
  - Feature descriptions
  - Usage instructions
  - Deployment options
  - Troubleshooting
  - Customization guide

### 📋 WEBSITE_SUMMARY.md (in parent directory)
- **Purpose**: Implementation overview
- **Covers**:
  - Design decisions
  - Technical architecture
  - Future enhancements
  - Performance characteristics

## How to Use These Files

### First Time Setup
1. Read `QUICKSTART.md`
2. Run `./serve.sh`
3. Open `http://localhost:8000/test.html` to validate
4. Open `http://localhost:8000/index.html` to view dashboard

### Development
- Edit `index.html` for layout/styling changes
- Edit `app.js` for functionality changes
- Refresh browser to see changes

### Deployment
- Copy entire `website` folder to web server
- Ensure `../data/json/` is accessible
- See README.md for deployment platform specifics

## File Dependencies

```
index.html
├── app.js (JavaScript logic)
├── Chart.js (CDN - external)
└── ../data/json/*.json (data files)

serve.sh
└── Python 3 (built-in HTTP server)

test.html
└── ../data/json/*.json (data files)
```

## Customization Quick Reference

### Change Colors
Edit CSS variables in `index.html`:
```css
:root {
    --primary: #1e40af;
    --success: #059669;
    --danger: #dc2626;
}
```

### Add New Chart
1. Add canvas element to `index.html`
2. Create render method in `app.js`
3. Call from `renderCharts()` method

### Modify Crime Categories
Edit `filterStatsByCategory()` in `app.js`

## File Sizes
- index.html: ~16KB
- app.js: ~20KB
- README.md: ~4KB
- QUICKSTART.md: ~3KB
- Total: ~43KB (very lightweight!)

## Browser Support
All files work with modern browsers (Chrome, Firefox, Safari, Edge).
Requires JavaScript enabled.
