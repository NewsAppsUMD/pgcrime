// Crime Statistics Dashboard Application

class CrimeDashboard {
    constructor() {
        this.data = null;
        this.availableDates = [];
        this.charts = {};
        // Configure data path - can be overridden by setting window.DATA_PATH
        this.dataPath = window.DATA_PATH || '../data/json/';
        console.log('Dashboard initialized with data path:', this.dataPath);
        this.init();
    }

    async init() {
        await this.loadAvailableDates();
        if (this.availableDates.length > 0) {
            await this.loadLatestData();
            this.setupEventListeners();
            this.renderSummaryCards();
            this.renderCharts();
            this.renderTable('all');
        } else {
            this.showNoDataMessage();
        }
    }

    showNoDataMessage() {
        const lastUpdated = document.getElementById('lastUpdated');
        lastUpdated.innerHTML = `
            <strong>⚠️ No data files found</strong><br>
            Looking for JSON files at: ${this.dataPath}<br>
            <small>Please ensure crime data JSON files exist in the data/json directory.</small>
        `;
        lastUpdated.style.color = '#fee2e2';
        lastUpdated.style.background = '#7f1d1d';
        lastUpdated.style.padding = '1rem';
        lastUpdated.style.borderRadius = '8px';
        lastUpdated.style.marginTop = '1rem';

        console.error('No data files found at:', this.dataPath);
        console.log('Tried to load files with format: YYYYMMDD.json');
        console.log('Example: 20260212.json for February 12, 2026');
    }

    async loadAvailableDates() {
        try {
            // Try to load dates from a manifest file or scan directory
            // For now, we'll try to load the most recent files
            const dates = [];
            const today = new Date();

            // Try to load the last 30 days
            for (let i = 0; i < 30; i++) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                const dateStr = this.formatDateForFile(date);

                try {
                    const response = await fetch(`${this.dataPath}${dateStr}.json`);
                    if (response.ok) {
                        dates.push(dateStr);
                    }
                } catch (e) {
                    // File doesn't exist, continue
                }
            }

            this.availableDates = dates.sort().reverse();
            this.populateDateSelector();
        } catch (error) {
            console.error('Error loading available dates:', error);
        }
    }

    formatDateForFile(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}${month}${day}`;
    }

    formatDateForDisplay(dateStr) {
        // Convert YYYYMMDD to readable format
        const year = dateStr.substring(0, 4);
        const month = dateStr.substring(4, 6);
        const day = dateStr.substring(6, 8);
        const date = new Date(year, parseInt(month) - 1, day);
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    populateDateSelector() {
        const select = document.getElementById('dateSelect');
        select.innerHTML = this.availableDates.map(date =>
            `<option value="${date}">${this.formatDateForDisplay(date)}</option>`
        ).join('');
    }

    async loadLatestData() {
        if (this.availableDates.length === 0) return;

        const latestDate = this.availableDates[0];
        await this.loadData(latestDate);
    }

    async loadData(dateStr) {
        try {
            const response = await fetch(`${this.dataPath}${dateStr}.json`);
            this.data = await response.json();

            // Update last updated text
            const lastUpdated = document.getElementById('lastUpdated');
            lastUpdated.textContent = `Last updated: ${this.formatDateForDisplay(dateStr)}`;

            return this.data;
        } catch (error) {
            console.error('Error loading data:', error);
            return null;
        }
    }

    setupEventListeners() {
        document.getElementById('dateSelect').addEventListener('change', async (e) => {
            await this.loadData(e.target.value);
            this.renderSummaryCards();
            this.updateCharts();
            const category = document.getElementById('categoryFilter').value;
            this.renderTable(category);
        });

        document.getElementById('categoryFilter').addEventListener('change', (e) => {
            this.renderTable(e.target.value);
        });
    }

    getStatByOffense(offenseName) {
        return this.data.crime_statistics.find(
            stat => stat.offense_type.toLowerCase() === offenseName.toLowerCase()
        );
    }

    renderSummaryCards() {
        if (!this.data) return;

        // Total Crime
        const totalCrime = this.getStatByOffense('Total Crime');
        if (totalCrime) {
            const pctChange = this.calculatePercentChange(totalCrime.ytd_2026, totalCrime.ytd_2025);
            document.getElementById('totalCrime7').innerHTML = this.formatCardValue(totalCrime.seven_day_total, totalCrime.ytd_2026, totalCrime.ytd_2025);
            document.getElementById('totalCrimeYTD').innerHTML = this.formatYTDComparison(totalCrime.ytd_2026, totalCrime.ytd_2025);
            document.getElementById('totalCrimeChange').innerHTML = this.formatChange(totalCrime.ytd_2026 - totalCrime.ytd_2025, pctChange);
        }

        // Violent Crime
        const violentCrime = this.getStatByOffense('Violent Crime Total');
        if (violentCrime) {
            const pctChange = this.calculatePercentChange(violentCrime.ytd_2026, violentCrime.ytd_2025);
            document.getElementById('violentCrime7').innerHTML = this.formatCardValue(violentCrime.seven_day_total, violentCrime.ytd_2026, violentCrime.ytd_2025);
            document.getElementById('violentCrimeYTD').innerHTML = this.formatYTDComparison(violentCrime.ytd_2026, violentCrime.ytd_2025);
            document.getElementById('violentCrimeChange').innerHTML = this.formatChange(violentCrime.ytd_2026 - violentCrime.ytd_2025, pctChange);
        }

        // Property Crime
        const propertyCrime = this.getStatByOffense('Property Crime Total');
        if (propertyCrime) {
            const pctChange = this.calculatePercentChange(propertyCrime.ytd_2026, propertyCrime.ytd_2025);
            document.getElementById('propertyCrime7').innerHTML = this.formatCardValue(propertyCrime.seven_day_total, propertyCrime.ytd_2026, propertyCrime.ytd_2025);
            document.getElementById('propertyCrimeYTD').innerHTML = this.formatYTDComparison(propertyCrime.ytd_2026, propertyCrime.ytd_2025);
            document.getElementById('propertyCrimeChange').innerHTML = this.formatChange(propertyCrime.ytd_2026 - propertyCrime.ytd_2025, pctChange);
        }

        // Homicides (Murder)
        const homicides = this.getStatByOffense('Murder');
        if (homicides) {
            const pctChange = this.calculatePercentChange(homicides.ytd_2026, homicides.ytd_2025);
            document.getElementById('homicide7').innerHTML = this.formatCardValue(homicides.seven_day_total, homicides.ytd_2026, homicides.ytd_2025);
            document.getElementById('homicideYTD').innerHTML = this.formatYTDComparison(homicides.ytd_2026, homicides.ytd_2025);
            document.getElementById('homicideChange').innerHTML = this.formatChange(homicides.ytd_2026 - homicides.ytd_2025, pctChange);
        }
    }

    calculatePercentChange(current, previous) {
        if (previous === 0) return current > 0 ? 100 : 0;
        return ((current - previous) / previous * 100).toFixed(1);
    }

    formatCardValue(sevenDay, ytd2026, ytd2025) {
        const pct = this.calculatePercentChange(ytd2026, ytd2025);
        const isDecrease = ytd2026 < ytd2025;
        const color = isDecrease ? '#059669' : (ytd2026 > ytd2025 ? '#dc2626' : '#64748b');

        return `
            <div style="display: flex; align-items: baseline; gap: 0.75rem;">
                <span style="font-size: 2.5rem; font-weight: 700;">${sevenDay}</span>
                <span style="font-size: 1.25rem; font-weight: 700; color: ${color};">
                    ${pct > 0 ? '+' : ''}${pct}%
                </span>
            </div>
            <div style="font-size: 0.875rem; color: #64748b; margin-top: 0.25rem;">
                7-day total
            </div>
        `;
    }

    formatYTDComparison(ytd2026, ytd2025) {
        const pct = this.calculatePercentChange(ytd2026, ytd2025);
        const isDecrease = ytd2026 < ytd2025;
        const color = isDecrease ? '#059669' : (ytd2026 > ytd2025 ? '#dc2626' : '#64748b');

        return `
            <div style="font-size: 1.5rem; font-weight: 700;">${ytd2026}</div>
            <div style="font-size: 0.875rem; color: #64748b;">2026 YTD</div>
        `;
    }

    formatChange(value, percentChange) {
        if (value === 0) {
            return '<span class="change-badge neutral">No Change</span>';
        } else if (value < 0) {
            return `<span class="change-badge positive arrow-down">${percentChange}% <span style="font-size: 0.875rem; opacity: 0.8;">(${value})</span></span>`;
        } else {
            return `<span class="change-badge negative arrow-up">+${percentChange}% <span style="font-size: 0.875rem; opacity: 0.8;">(+${value})</span></span>`;
        }
    }

    renderCharts() {
        this.renderYTDOverallChart();
        this.renderYTDHighProfileChart();
        this.renderYTDPropertyChart();
        this.renderSevenDayComparisonChart();
        this.renderDailyBreakdownChart();
    }

    updateCharts() {
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};
        this.renderCharts();
    }

    renderYTDOverallChart() {
        const ctx = document.getElementById('ytdOverallChart').getContext('2d');

        const totalCrime = this.getStatByOffense('Total Crime');
        const violentCrime = this.getStatByOffense('Violent Crime Total');
        const propertyCrime = this.getStatByOffense('Property Crime Total');

        const stats = [totalCrime, violentCrime, propertyCrime];

        this.charts.ytdOverall = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Total Crime', 'Violent Crime', 'Property Crime'],
                datasets: [{
                    label: '2026 YTD',
                    data: [totalCrime?.ytd_2026 || 0, violentCrime?.ytd_2026 || 0, propertyCrime?.ytd_2026 || 0],
                    backgroundColor: 'rgba(0, 61, 165, 0.85)',
                    borderColor: 'rgba(0, 61, 165, 1)',
                    borderWidth: 2
                }, {
                    label: '2025 YTD',
                    data: [totalCrime?.ytd_2025 || 0, violentCrime?.ytd_2025 || 0, propertyCrime?.ytd_2025 || 0],
                    backgroundColor: 'rgba(255, 184, 28, 0.75)',
                    borderColor: 'rgba(255, 184, 28, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            afterLabel: function(context) {
                                const datasetIndex = context.datasetIndex;
                                const index = context.dataIndex;
                                if (datasetIndex === 0) {
                                    const current = context.parsed.y;
                                    const previous = context.chart.data.datasets[1].data[index];
                                    const change = current - previous;
                                    const pct = previous > 0 ? ((change / previous) * 100).toFixed(1) : 0;
                                    const sign = change > 0 ? '+' : '';
                                    return `YTD Change: ${sign}${pct}% (${sign}${change})`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Add percentage labels above 2026 bars
        this.addPercentageLabels(ctx, stats);
    }

    addPercentageLabels(ctx, stats) {
        // Store stats for later use in drawing labels
        ctx.canvas.dataset.stats = JSON.stringify(stats.map(s => ({
            ytd_2026: s?.ytd_2026 || 0,
            ytd_2025: s?.ytd_2025 || 0
        })));
    }

    renderYTDHighProfileChart() {
        const ctx = document.getElementById('ytdHighProfileChart').getContext('2d');

        const offenses = ['Murder', 'Robbery', 'Carjacking', 'Non-Fatal Shooting'];
        const stats = offenses.map(o => this.getStatByOffense(o));

        this.charts.ytdHighProfile = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: offenses,
                datasets: [{
                    label: '2026 YTD',
                    data: stats.map(s => s?.ytd_2026 || 0),
                    backgroundColor: 'rgba(0, 61, 165, 0.85)',
                    borderColor: 'rgba(0, 61, 165, 1)',
                    borderWidth: 2
                }, {
                    label: '2025 YTD',
                    data: stats.map(s => s?.ytd_2025 || 0),
                    backgroundColor: 'rgba(255, 184, 28, 0.75)',
                    borderColor: 'rgba(255, 184, 28, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const datasetIndex = context.datasetIndex;
                                const index = context.dataIndex;
                                if (datasetIndex === 0) {
                                    const current = context.parsed.y;
                                    const previous = context.chart.data.datasets[1].data[index];
                                    const change = current - previous;
                                    const pct = previous > 0 ? ((change / previous) * 100).toFixed(1) : (current > 0 ? 100 : 0);
                                    const sign = change > 0 ? '+' : '';
                                    return `YTD Change: ${sign}${pct}% (${sign}${change})`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    renderYTDPropertyChart() {
        const ctx = document.getElementById('ytdPropertyChart').getContext('2d');

        const offenses = ['Burglary', 'Larceny', 'Stolen Vehicle'];
        const stats = offenses.map(o => this.getStatByOffense(o));

        this.charts.ytdProperty = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: offenses,
                datasets: [{
                    label: '2026 YTD',
                    data: stats.map(s => s?.ytd_2026 || 0),
                    backgroundColor: 'rgba(0, 61, 165, 0.85)',
                    borderColor: 'rgba(0, 61, 165, 1)',
                    borderWidth: 2
                }, {
                    label: '2025 YTD',
                    data: stats.map(s => s?.ytd_2025 || 0),
                    backgroundColor: 'rgba(255, 184, 28, 0.75)',
                    borderColor: 'rgba(255, 184, 28, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const datasetIndex = context.datasetIndex;
                                const index = context.dataIndex;
                                if (datasetIndex === 0) {
                                    const current = context.parsed.y;
                                    const previous = context.chart.data.datasets[1].data[index];
                                    const change = current - previous;
                                    const pct = previous > 0 ? ((change / previous) * 100).toFixed(1) : (current > 0 ? 100 : 0);
                                    const sign = change > 0 ? '+' : '';
                                    return `YTD Change: ${sign}${pct}% (${sign}${change})`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    renderSevenDayComparisonChart() {
        const ctx = document.getElementById('sevenDayComparisonChart').getContext('2d');

        const violentCrime = this.getStatByOffense('Violent Crime Total');
        const propertyCrime = this.getStatByOffense('Property Crime Total');

        this.charts.sevenDay = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Violent Crime', 'Property Crime'],
                datasets: [{
                    label: 'Last 7 Days',
                    data: [violentCrime?.seven_day_total || 0, propertyCrime?.seven_day_total || 0],
                    backgroundColor: 'rgba(0, 61, 165, 0.85)',
                    borderColor: 'rgba(0, 61, 165, 1)',
                    borderWidth: 2
                }, {
                    label: 'Previous 7 Days',
                    data: [violentCrime?.prev_seven_day_total || 0, propertyCrime?.prev_seven_day_total || 0],
                    backgroundColor: 'rgba(255, 184, 28, 0.75)',
                    borderColor: 'rgba(255, 184, 28, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const datasetIndex = context.datasetIndex;
                                const index = context.dataIndex;
                                if (datasetIndex === 0) {
                                    const current = context.parsed.y;
                                    const previous = context.chart.data.datasets[1].data[index];
                                    const change = current - previous;
                                    return `Change: ${change > 0 ? '+' : ''}${change}`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    renderDailyBreakdownChart() {
        const ctx = document.getElementById('dailyBreakdownChart').getContext('2d');

        const totalCrime = this.getStatByOffense('Total Crime');
        const violentCrime = this.getStatByOffense('Violent Crime Total');
        const propertyCrime = this.getStatByOffense('Property Crime Total');

        if (!totalCrime) return;

        // Extract daily data from the last 7 days
        const dailyFields = Object.keys(totalCrime).filter(key => key.match(/^\d{4}-\d{2}-\d{2}$/));
        const labels = dailyFields.map(date => {
            const d = new Date(date);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const totalData = dailyFields.map(field => totalCrime[field]);
        const violentData = dailyFields.map(field => violentCrime[field]);
        const propertyData = dailyFields.map(field => propertyCrime[field]);

        this.charts.dailyBreakdown = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Total Crime',
                    data: totalData,
                    borderColor: 'rgba(0, 61, 165, 1)',
                    backgroundColor: 'rgba(0, 61, 165, 0.15)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: 'rgba(0, 61, 165, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }, {
                    label: 'Violent Crime',
                    data: violentData,
                    borderColor: 'rgba(220, 38, 38, 1)',
                    backgroundColor: 'rgba(220, 38, 38, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: 'rgba(220, 38, 38, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 3
                }, {
                    label: 'Property Crime',
                    data: propertyData,
                    borderColor: 'rgba(255, 184, 28, 1)',
                    backgroundColor: 'rgba(255, 184, 28, 0.15)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: 'rgba(255, 184, 28, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    renderTable(category) {
        if (!this.data) return;

        const tbody = document.getElementById('crimeTableBody');
        const stats = this.filterStatsByCategory(category);

        tbody.innerHTML = stats.map(stat => {
            // Skip the header row
            if (typeof stat.seven_day_total === 'string') return '';

            const ytdChange = stat.ytd_2026 - stat.ytd_2025;
            const weekChange = stat.seven_day_total - stat.prev_seven_day_total;
            const ytdPct = this.calculatePercentChange(stat.ytd_2026, stat.ytd_2025);

            return `
                <tr>
                    <td class="offense-name">${stat.offense_type}</td>
                    <td class="num-cell">${stat.seven_day_total}</td>
                    <td class="num-cell">${stat.prev_seven_day_total}</td>
                    <td class="num-cell">${this.formatTableChange(weekChange)}</td>
                    <td class="num-cell"><strong>${stat.ytd_2026}</strong></td>
                    <td class="num-cell">${stat.ytd_2025}</td>
                    <td class="num-cell">${this.formatTableChangeWithPercent(ytdChange, ytdPct)}</td>
                </tr>
            `;
        }).join('');
    }

    formatTableChange(value) {
        if (value === 0) {
            return '<span style="color: #64748b;">0</span>';
        } else if (value < 0) {
            return `<span style="color: #059669; font-weight: 600;">${value}</span>`;
        } else {
            return `<span style="color: #dc2626; font-weight: 600;">+${value}</span>`;
        }
    }

    formatTableChangeWithPercent(value, pct) {
        if (value === 0) {
            return '<span style="color: #64748b;">0%</span>';
        } else if (value < 0) {
            return `<span style="color: #059669; font-weight: 700;">${pct}% <span style="font-size: 0.875em; opacity: 0.7;">(${value})</span></span>`;
        } else {
            return `<span style="color: #dc2626; font-weight: 700;">+${pct}% <span style="font-size: 0.875em; opacity: 0.7;">(+${value})</span></span>`;
        }
    }

    filterStatsByCategory(category) {
        if (!this.data) return [];

        const highProfileOffenses = [
            'Murder', 'Robbery', 'Carjacking', 'Non-Fatal Shooting',
            'Assault', 'Sex Offense', 'Rape'
        ];

        const violentOffenses = [
            'Murder', 'Sex Offense', 'Rape', 'Fondling', 'Robbery',
            'Commercial Robbery', 'Residential Robbery', 'Citizen Robbery',
            'Carjacking', 'Assault', 'Non-Fatal Shooting',
            'Assault (Other Weapon)', 'Assault (No Weapon)',
            'Violent Crime Total'
        ];

        const propertyOffenses = [
            'Burglary', 'Commercial Burglary', 'Residential Burglary',
            'Other Burglary', 'Larceny', 'Theft from Auto', 'Other Theft',
            'Stolen Vehicle', 'Property Crime Total'
        ];

        return this.data.crime_statistics.filter(stat => {
            // Skip header rows
            if (typeof stat.seven_day_total === 'string') return false;

            switch (category) {
                case 'violent':
                    return violentOffenses.includes(stat.offense_type);
                case 'property':
                    return propertyOffenses.includes(stat.offense_type);
                case 'high-profile':
                    return highProfileOffenses.includes(stat.offense_type);
                case 'all':
                default:
                    return true;
            }
        });
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new CrimeDashboard();
});
