// API Base URL
const API_BASE = 'http://localhost:8000/api';

// State
let currentFilter = 'all';
let statusChart = null;
let alertTrendChart = null;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    loadDashboardData();
    setupFilters();
    setupAutoRefresh();
});

// Setup Filter Buttons
function setupFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            loadAlerts();
        });
    });
}

// Setup Auto Refresh
function setupAutoRefresh() {
    setInterval(() => {
        loadDashboardData();
    }, 30000); // 30 seconds
}

// Load All Dashboard Data
async function loadDashboardData() {
    try {
        await Promise.all([
            loadSummary(),
            loadAlerts(),
            loadEvents(),
            updateCharts()
        ]);
        updateLastUpdateTime();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Load Summary Statistics
async function loadSummary() {
    try {
        const [domainsRes, alertsRes, eventsRes] = await Promise.all([
            fetch(`${API_BASE}/domains?limit=1000`),
            fetch(`${API_BASE}/alerts?is_resolved=false&limit=1000`),
            fetch(`${API_BASE}/events?limit=1000`)
        ]);

        const domains = await domainsRes.json();
        const alerts = await alertsRes.json();
        const events = await eventsRes.json();

        // Calculate statistics
        const totalDomains = domains.length;
        const activeDomains = domains.filter(d => d.is_active).length;
        
        // 統計告警等級
        const p0Alerts = alerts.filter(a => a.alert_level === 'P0').length;
        const p1Alerts = alerts.filter(a => a.alert_level === 'P1').length;
        const p2Alerts = alerts.filter(a => a.alert_level === 'P2').length;
        
        // 統計有告警的唯一域名數量
        const domainsWithAlerts = new Set(alerts.map(a => a.domain_id)).size;
        
        // 從最近的監控事件中統計正常的域名
        const recentEvents = events.filter(e => 
            e.event_type === 'dns_check' && 
            new Date(e.timestamp) > new Date(Date.now() - 10 * 60 * 1000) // 最近 10 分鐘
        );
        
        // 按 domain_id 分組,取最新的狀態
        const latestStatusByDomain = {};
        recentEvents.forEach(event => {
            if (!latestStatusByDomain[event.domain_id] || 
                new Date(event.timestamp) > new Date(latestStatusByDomain[event.domain_id].timestamp)) {
                latestStatusByDomain[event.domain_id] = event;
            }
        });
        
        const healthyDomains = Object.values(latestStatusByDomain)
            .filter(e => e.status === 'ok').length;
        
        const warningDomains = domainsWithAlerts;

        // Update UI
        document.getElementById('totalDomains').textContent = totalDomains;
        document.getElementById('healthyDomains').textContent = healthyDomains;
        document.getElementById('warningDomains').textContent = warningDomains;
        document.getElementById('criticalAlerts').textContent = p0Alerts;

        // Update charts data
        updateStatusChart(healthyDomains, warningDomains, p0Alerts);
        
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

// Load Alerts
async function loadAlerts() {
    try {
        const response = await fetch(`${API_BASE}/alerts?is_resolved=false&limit=20`);
        const alerts = await response.json();

        const filteredAlerts = currentFilter === 'all' 
            ? alerts 
            : alerts.filter(a => a.alert_level === currentFilter);

        const container = document.getElementById('alertsContainer');
        
        if (filteredAlerts.length === 0) {
            container.innerHTML = '<div class="loading">暫無告警 ✨</div>';
            return;
        }

        container.innerHTML = filteredAlerts.map(alert => `
            <div class="alert-item ${alert.alert_level}">
                <div class="alert-header">
                    <span class="alert-domain">${alert.domain_name || `Domain #${alert.domain_id}`}</span>
                    <span class="alert-badge ${alert.alert_level}">${alert.alert_level}</span>
                </div>
                <div class="alert-cause">
                    ${getRootCauseText(alert.root_cause)}
                </div>
                <div class="alert-time">
                    首次發現: ${formatTime(alert.first_seen)} | 
                    最後更新: ${formatTime(alert.last_seen)}
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading alerts:', error);
        document.getElementById('alertsContainer').innerHTML = 
            '<div class="loading">載入失敗</div>';
    }
}

// Load Recent Events
async function loadEvents() {
    try {
        const response = await fetch(`${API_BASE}/events?limit=15`);
        const events = await response.json();

        const container = document.getElementById('eventsContainer');
        
        if (events.length === 0) {
            container.innerHTML = '<div class="loading">暫無事件</div>';
            return;
        }

        container.innerHTML = events.map(event => `
            <div class="event-item">
                <div class="event-info">
                    <div class="event-status ${event.status}"></div>
                    <div>
                        <div class="event-domain">Domain #${event.domain_id}</div>
                        <div class="event-type">${getEventTypeText(event.event_type)}</div>
                    </div>
                </div>
                <div class="event-time">${formatTime(event.timestamp)}</div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading events:', error);
        document.getElementById('eventsContainer').innerHTML = 
            '<div class="loading">載入失敗</div>';
    }
}

// Initialize Charts
function initCharts() {
    const statusCtx = document.getElementById('statusChart').getContext('2d');
    const alertTrendCtx = document.getElementById('alertTrendChart').getContext('2d');

    statusChart = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['正常', '警告', '嚴重'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(245, 158, 11, 1)',
                    'rgba(239, 68, 68, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e4e6eb',
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });

    alertTrendChart = new Chart(alertTrendCtx, {
        type: 'line',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [{
                label: 'P0 告警',
                data: Array(24).fill(0),
                borderColor: 'rgba(239, 68, 68, 1)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4
            }, {
                label: 'P1 告警',
                data: Array(24).fill(0),
                borderColor: 'rgba(245, 158, 11, 1)',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e4e6eb',
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });
}

// Update Status Chart
function updateStatusChart(healthy, warning, critical) {
    if (statusChart) {
        statusChart.data.datasets[0].data = [healthy, warning, critical];
        statusChart.update();
    }
}

// Update Charts with Real Data
async function updateCharts() {
    try {
        const response = await fetch(`${API_BASE}/alerts?limit=100`);
        const alerts = await response.json();

        // Generate mock trend data (in real scenario, you'd aggregate from events)
        const p0Trend = Array(24).fill(0);
        const p1Trend = Array(24).fill(0);

        alerts.forEach(alert => {
            const hour = new Date(alert.first_seen).getHours();
            if (alert.alert_level === 'P0') p0Trend[hour]++;
            if (alert.alert_level === 'P1') p1Trend[hour]++;
        });

        if (alertTrendChart) {
            alertTrendChart.data.datasets[0].data = p0Trend;
            alertTrendChart.data.datasets[1].data = p1Trend;
            alertTrendChart.update();
        }

    } catch (error) {
        console.error('Error updating charts:', error);
    }
}

// Helper Functions
function getRootCauseText(cause) {
    const causes = {
        'domain_hijacked': '🚨 域名劫持 - Nameserver 已變更',
        'isp_blocked': '⚠️ ISP 封鎖 - 區域性 DNS 污染',
        'content_defacement': '⚠️ 內容竄改 - 網頁內容異常',
        'config_error': 'ℹ️ 配置錯誤 - DNS 解析失敗',
        'whois_changed': 'ℹ️ WHOIS 變動 - 註冊資訊更新'
    };
    return causes[cause] || cause;
}

function getEventTypeText(type) {
    const types = {
        'dns_check': 'DNS 檢查',
        'uptime_check': '可用性檢查',
        'whois_check': 'WHOIS 檢查'
    };
    return types[type] || type;
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return `${diff} 秒前`;
    if (diff < 3600) return `${Math.floor(diff / 60)} 分鐘前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小時前`;
    
    return date.toLocaleString('zh-TW', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = 
        now.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

