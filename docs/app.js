// Crime Statistics Dashboard Application

class CrimeDashboard {
    constructor() {
        this.data = null;
        this.availableDates = [];
        this.replayDates = [];
        this.lastCheck = null;
        this.charts = {};
        this.historicalChart = null;
        this.timeseries = null;
        this.dataCache = {};
        this.replayTimer = null;
        // Configure data path - can be overridden by setting window.DATA_PATH
        this.dataPath = window.DATA_PATH || '../data/json/';
        console.log('Dashboard initialized');
        console.log('Data path:', this.dataPath);
        console.log('Attempting to load from:', this.dataPath + 'manifest.json');
        this.init();
    }

    async init() {
        await this.loadAvailableDates();
        if (this.availableDates.length > 0) {
            await this.loadTimeseries();
            this.setupEventListeners();
            this.setupReplayControls();
            this.renderHistoricalTrendChart();
            await this.showDate(this.availableDates[0]);
        } else {
            this.showNoDataMessage();
        }
    }

    // Fetch with revalidation so browsers don't serve stale cached JSON
    // (e.g., an old manifest.json showing an outdated "Last updated" date).
    // 'no-cache' still honors ETag/Last-Modified, so unchanged files are cheap.
    fetchFresh(url) {
        return fetch(url, { cache: 'no-cache' });
    }

    async loadTimeseries() {
        try {
            const response = await this.fetchFresh(`${this.dataPath}timeseries.json`);
            if (response.ok) {
                this.timeseries = await response.json();
            } else {
                console.warn('Timeseries not available:', response.status);
            }
        } catch (e) {
            console.warn('Timeseries fetch failed:', e.message);
        }
    }

    async showDate(dateStr) {
        await this.loadData(dateStr);
        this.renderSummaryCards();
        this.renderTrendSummary();
        this.renderNotableAlerts();
        this.updateCharts();
        const category = document.getElementById('categoryFilter').value;
        this.renderTable(category);
        document.getElementById('dateSelect').value = dateStr;
        const slider = document.getElementById('replaySlider');
        if (slider) {
            slider.value = this.replayDates.indexOf(dateStr);
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
            // Try to load from manifest file first (more reliable for static hosting)
            try {
                const manifestUrl = `${this.dataPath}manifest.json`;
                console.log('Fetching manifest from:', manifestUrl);
                const manifestResponse = await this.fetchFresh(manifestUrl);
                console.log('Manifest response status:', manifestResponse.status);
                if (manifestResponse.ok) {
                    const manifest = await manifestResponse.json();
                    this.availableDates = manifest.files
                        .map(f => f.replace('.json', ''))
                        .sort()
                        .reverse();
                    this.lastCheck = manifest.last_check || null;
                    this.populateDateSelector();
                    console.log('Loaded dates from manifest:', this.availableDates);
                    return;
                } else {
                    console.warn('Manifest returned status:', manifestResponse.status);
                }
            } catch (e) {
                console.warn('Manifest fetch failed:', e.message);
                console.log('Falling back to file probing');
            }

            // Fallback: try to load the most recent files
            const dates = [];
            const today = new Date();

            // Try to load the last 30 days
            for (let i = 0; i < 30; i++) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                const dateStr = this.formatDateForFile(date);

                try {
                    const response = await this.fetchFresh(`${this.dataPath}${dateStr}.json`);
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
            if (this.dataCache[dateStr]) {
                this.data = this.dataCache[dateStr];
            } else {
                const response = await this.fetchFresh(`${this.dataPath}${dateStr}.json`);
                this.data = await response.json();
                this.dataCache[dateStr] = this.data;
            }

            // Update last updated text
            const lastUpdated = document.getElementById('lastUpdated');
            let html = `Last updated: ${this.formatDateForDisplay(dateStr)}`;
            // Only warn about missing reports when viewing the latest data
            if (dateStr === this.availableDates[0]) {
                html += this.getStalenessWarning(dateStr);
            }
            lastUpdated.innerHTML = html;

            return this.data;
        } catch (error) {
            console.error('Error loading data:', error);
            return null;
        }
    }

    getStalenessWarning(latestDateStr) {
        // Reports are published with a one-day lag, so the newest report
        // should normally be dated yesterday. Anything older means the
        // county hasn't posted a new PDF.
        const year = parseInt(latestDateStr.substring(0, 4));
        const month = parseInt(latestDateStr.substring(4, 6)) - 1;
        const day = parseInt(latestDateStr.substring(6, 8));
        const latest = new Date(year, month, day);

        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        yesterday.setHours(0, 0, 0, 0);

        const missingDays = Math.round((yesterday - latest) / (1000 * 60 * 60 * 24));
        if (missingDays <= 0) return '';

        const checkedText = this.lastCheck
            ? `last checked ${new Date(this.lastCheck).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`
            : 'checked daily';

        return `<span class="staleness-warning">⚠️ No new report published in ${missingDays} day${missingDays === 1 ? '' : 's'} — the updater is still running (${checkedText}); the county has not posted a new PDF.</span>`;
    }

    renderTrendSummary() {
        const el = document.getElementById('trendSummary');
        if (!el || !this.data) return;

        const total = this.getStatByOffense('Total Crime');
        if (!total) return;

        const weekPct = Number(this.calculatePercentChange(total.seven_day_total, total.prev_seven_day_total));
        let weekText;
        if (total.seven_day_total === total.prev_seven_day_total) {
            weekText = `held steady at ${total.seven_day_total} incidents`;
        } else {
            const dir = total.seven_day_total > total.prev_seven_day_total ? 'up' : 'down';
            weekText = `was ${dir} ${Math.abs(weekPct)}% from the prior week (${total.seven_day_total} vs ${total.prev_seven_day_total} incidents)`;
        }

        const ytdPct = Number(this.calculatePercentChange(total.ytd_2026, total.ytd_2025));
        const ytdDir = total.ytd_2026 >= total.ytd_2025 ? 'above' : 'below';

        // Biggest week-over-week mover among main offense categories
        const excluded = new Set(['Total Crime', 'Violent Crime Total', 'Property Crime Total', 'DCR Offense - NON-VIOLENT']);
        const seen = new Set();
        let mover = null;
        for (const s of this.data.crime_statistics) {
            if (excluded.has(s.offense_type) || seen.has(s.offense_type)) continue;
            seen.add(s.offense_type);
            if (Math.max(s.seven_day_total, s.prev_seven_day_total) < 3) continue;
            const pct = Math.abs(Number(this.calculatePercentChange(s.seven_day_total, s.prev_seven_day_total)));
            if (!mover || pct > mover.absPct) {
                mover = { name: s.offense_type, cur: s.seven_day_total, prev: s.prev_seven_day_total, absPct: pct };
            }
        }

        const weekEnding = this.data.report_date
            ? new Date(this.data.report_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
            : '';

        let html = `<strong>Week ending ${weekEnding}:</strong> total crime ${weekText}. Year to date, total crime is running ${Math.abs(ytdPct)}% ${ytdDir} 2025.`;
        if (mover) {
            const mDir = mover.cur >= mover.prev ? 'up' : 'down';
            html += ` Biggest mover: <strong>${mover.name}</strong>, ${mDir} ${Math.round(mover.absPct)}% week over week (${mover.cur} vs ${mover.prev}).`;
        }
        el.innerHTML = html;
    }

    renderNotableAlerts() {
        const el = document.getElementById('alertsStrip');
        if (!el || !this.data) return;

        // High-profile offenses always alert on any week-over-week change.
        const alwaysAlert = new Set(['Murder', 'Non-Fatal Shooting', 'Carjacking', 'Robbery']);
        // Sub-categories and totals are excluded to avoid duplicate noise.
        const excluded = new Set([
            'Total Crime', 'Violent Crime Total', 'Property Crime Total', 'DCR Offense - NON-VIOLENT',
            'Commercial Robbery', 'Residential Robbery', 'Citizen Robbery',
            'Commercial Burglary', 'Residential Burglary', 'Other Burglary',
            'DV Non-Fatal Shooting', 'DV Assault (Other Weapon)', 'DV Assault (No Weapon)',
            'Assault (Other Weapon)', 'Assault (No Weapon)', 'Fondling', 'Rape'
        ]);

        const seen = new Set();
        const alerts = [];
        for (const s of this.data.crime_statistics) {
            if (excluded.has(s.offense_type) || seen.has(s.offense_type)) continue;
            seen.add(s.offense_type);
            const diff = s.seven_day_total - s.prev_seven_day_total;
            if (diff === 0) continue;
            const pct = Math.abs(Number(this.calculatePercentChange(s.seven_day_total, s.prev_seven_day_total)));
            const significant = pct >= 25 && Math.max(s.seven_day_total, s.prev_seven_day_total) >= 5;
            if (alwaysAlert.has(s.offense_type) || significant) {
                alerts.push({ name: s.offense_type, diff, cur: s.seven_day_total, prev: s.prev_seven_day_total });
            }
        }

        alerts.sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));

        if (alerts.length === 0) {
            el.innerHTML = '';
            el.style.display = 'none';
            return;
        }

        el.style.display = 'flex';
        el.innerHTML = alerts.slice(0, 6).map(a => {
            const up = a.diff > 0;
            return `<span class="alert-badge ${up ? 'up' : 'down'}">${up ? '▲' : '▼'} ${a.name}: ${a.prev} → ${a.cur}</span>`;
        }).join('');
    }

    renderHistoricalTrendChart() {
        const canvas = document.getElementById('historicalTrendChart');
        if (!canvas || !this.timeseries) return;

        const ctx = canvas.getContext('2d');
        const ts = this.timeseries;

        const labels = ts.dates.map(d => {
            const dt = new Date(d + 'T00:00:00');
            return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        const getSeries = name => (ts.offenses[name] ? ts.offenses[name].seven_day_total : []);

        this.historicalChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Total Crime',
                    data: getSeries('Total Crime'),
                    borderColor: 'rgba(0, 61, 165, 1)',
                    backgroundColor: 'rgba(0, 61, 165, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 0
                }, {
                    label: 'Violent Crime',
                    data: getSeries('Violent Crime Total'),
                    borderColor: 'rgba(220, 38, 38, 1)',
                    backgroundColor: 'rgba(220, 38, 38, 0.08)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 0
                }, {
                    label: 'Property Crime',
                    data: getSeries('Property Crime Total'),
                    borderColor: 'rgba(255, 184, 28, 1)',
                    backgroundColor: 'rgba(255, 184, 28, 0.12)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: { beginAtZero: true },
                    x: { ticks: { maxTicksLimit: 16 } }
                },
                interaction: { mode: 'nearest', axis: 'x', intersect: false }
            }
        });
    }

    setupReplayControls() {
        const slider = document.getElementById('replaySlider');
        const btn = document.getElementById('replayBtn');
        if (!slider || !btn) return;

        // Chronological order: oldest report first.
        this.replayDates = [...this.availableDates].reverse();
        slider.min = 0;
        slider.max = this.replayDates.length - 1;
        slider.value = this.replayDates.length - 1;

        slider.addEventListener('input', async (e) => {
            this.stopReplay();
            await this.showDate(this.replayDates[Number(e.target.value)]);
        });

        btn.addEventListener('click', () => {
            if (this.replayTimer) {
                this.stopReplay();
            } else {
                this.startReplay();
            }
        });
    }

    startReplay() {
        const btn = document.getElementById('replayBtn');
        const slider = document.getElementById('replaySlider');
        let i = Number(slider.value);
        if (i >= this.replayDates.length - 1) i = 0; // restart from the beginning

        btn.textContent = '⏸ Pause';
        btn.classList.add('playing');

        // Prefetch all reports in the background so playback is smooth.
        for (const d of this.replayDates) {
            if (!this.dataCache[d]) {
                this.fetchFresh(`${this.dataPath}${d}.json`)
                    .then(r => r.ok ? r.json() : null)
                    .then(j => { if (j) this.dataCache[d] = j; })
                    .catch(() => {});
            }
        }

        this.replayTimer = setInterval(async () => {
            slider.value = i;
            await this.showDate(this.replayDates[i]);
            i++;
            if (i >= this.replayDates.length) this.stopReplay();
        }, 500);
    }

    stopReplay() {
        if (this.replayTimer) {
            clearInterval(this.replayTimer);
            this.replayTimer = null;
        }
        const btn = document.getElementById('replayBtn');
        if (btn) {
            btn.textContent = '▶ Replay';
            btn.classList.remove('playing');
        }
    }

    setupEventListeners() {
        document.getElementById('dateSelect').addEventListener('change', async (e) => {
            this.stopReplay();
            await this.showDate(e.target.value);
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
            const ytdPctChange = this.calculatePercentChange(totalCrime.ytd_2026, totalCrime.ytd_2025);
            const weekPctChange = this.calculatePercentChange(totalCrime.seven_day_total, totalCrime.prev_seven_day_total);
            document.getElementById('totalCrime7').innerHTML = this.formatCardValue(totalCrime.seven_day_total, totalCrime.prev_seven_day_total, weekPctChange);
            document.getElementById('totalCrimeYTD').innerHTML = this.formatYTDComparison(totalCrime.ytd_2026, totalCrime.ytd_2025);
            document.getElementById('totalCrimeChange').innerHTML = this.formatChange(totalCrime.ytd_2026 - totalCrime.ytd_2025, ytdPctChange);
        }

        // Violent Crime
        const violentCrime = this.getStatByOffense('Violent Crime Total');
        if (violentCrime) {
            const ytdPctChange = this.calculatePercentChange(violentCrime.ytd_2026, violentCrime.ytd_2025);
            const weekPctChange = this.calculatePercentChange(violentCrime.seven_day_total, violentCrime.prev_seven_day_total);
            document.getElementById('violentCrime7').innerHTML = this.formatCardValue(violentCrime.seven_day_total, violentCrime.prev_seven_day_total, weekPctChange);
            document.getElementById('violentCrimeYTD').innerHTML = this.formatYTDComparison(violentCrime.ytd_2026, violentCrime.ytd_2025);
            document.getElementById('violentCrimeChange').innerHTML = this.formatChange(violentCrime.ytd_2026 - violentCrime.ytd_2025, ytdPctChange);
        }

        // Property Crime
        const propertyCrime = this.getStatByOffense('Property Crime Total');
        if (propertyCrime) {
            const ytdPctChange = this.calculatePercentChange(propertyCrime.ytd_2026, propertyCrime.ytd_2025);
            const weekPctChange = this.calculatePercentChange(propertyCrime.seven_day_total, propertyCrime.prev_seven_day_total);
            document.getElementById('propertyCrime7').innerHTML = this.formatCardValue(propertyCrime.seven_day_total, propertyCrime.prev_seven_day_total, weekPctChange);
            document.getElementById('propertyCrimeYTD').innerHTML = this.formatYTDComparison(propertyCrime.ytd_2026, propertyCrime.ytd_2025);
            document.getElementById('propertyCrimeChange').innerHTML = this.formatChange(propertyCrime.ytd_2026 - propertyCrime.ytd_2025, ytdPctChange);
        }

        // Homicides (Murder)
        const homicides = this.getStatByOffense('Murder');
        if (homicides) {
            const ytdPctChange = this.calculatePercentChange(homicides.ytd_2026, homicides.ytd_2025);
            const weekPctChange = this.calculatePercentChange(homicides.seven_day_total, homicides.prev_seven_day_total);
            document.getElementById('homicide7').innerHTML = this.formatCardValue(homicides.seven_day_total, homicides.prev_seven_day_total, weekPctChange);
            document.getElementById('homicideYTD').innerHTML = this.formatYTDComparison(homicides.ytd_2026, homicides.ytd_2025);
            document.getElementById('homicideChange').innerHTML = this.formatChange(homicides.ytd_2026 - homicides.ytd_2025, ytdPctChange);
        }
    }

    calculatePercentChange(current, previous) {
        if (previous === 0) return current > 0 ? 100 : 0;
        return ((current - previous) / previous * 100).toFixed(1);
    }

    formatCardValue(sevenDayCurrent, sevenDayPrevious, pct) {
        const isDecrease = sevenDayCurrent < sevenDayPrevious;
        const color = isDecrease ? '#059669' : (sevenDayCurrent > sevenDayPrevious ? '#dc2626' : '#64748b');

        return `
            <div style="display: flex; align-items: baseline; gap: 0.75rem;">
                <span style="font-size: 2.5rem; font-weight: 700;">${sevenDayCurrent}</span>
                <span style="font-size: 1.25rem; font-weight: 700; color: ${color};">
                    ${pct > 0 ? '+' : ''}${pct}%
                </span>
            </div>
            <div style="font-size: 0.875rem; color: #64748b; margin-top: 0.25rem;">
                7-day total <span style="font-size: 0.75rem; opacity: 0.8;">(vs prev. 7 days)</span>
            </div>
        `;
    }

    formatYTDComparison(ytd2026, ytd2025) {
        const pct = this.calculatePercentChange(ytd2026, ytd2025);
        const isDecrease = ytd2026 < ytd2025;
        const color = isDecrease ? '#059669' : (ytd2026 > ytd2025 ? '#dc2626' : '#64748b');

        return `
            <div style="font-size: 1.5rem; font-weight: 700;">${ytd2026}</div>
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
