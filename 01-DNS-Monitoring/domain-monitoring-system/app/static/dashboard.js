// API Base URL
const API_BASE = 'http://localhost:8000/api';

// State
let currentFilter = 'all';
let statusChart = null;
let alertTrendChart = null;
let allDnsServers = [];
let currentCountry = 'all';

// 國家旗幟和名稱映射
const countryFlags = {
    'VN': '🇻🇳', 'ID': '🇮🇩', 'CN': '🇨🇳', 'TW': '🇹🇼', 'HK': '🇭🇰',
    'JP': '🇯🇵', 'KR': '🇰🇷', 'SG': '🇸🇬', 'TH': '🇹🇭', 'MY': '🇲🇾',
    'US': '🇺🇸', 'DE': '🇩🇪', 'CH': '🇨🇭', 'CY': '🇨🇾', 'AU': '🇦🇺'
};

const countryNames = {
    'VN': '越南', 'ID': '印尼', 'CN': '中國', 'TW': '台灣', 'HK': '香港',
    'JP': '日本', 'KR': '韓國', 'SG': '新加坡', 'TH': '泰國', 'MY': '馬來西亞',
    'US': '美國', 'DE': '德國', 'CH': '瑞士', 'CY': '塞浦路斯', 'AU': '澳洲'
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    initCharts();
    loadDashboardData();
    setupFilters();
    setupAutoRefresh();
    setupDomainTest();
});

// 設置標籤切換
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.dataset.tab;
            
            // 移除所有 active 類
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 添加 active 類到當前標籤
            button.classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.add('active');
            
            // 如果切換到 DNS 監控器標籤，載入 DNS 數據
            if (tabId === 'dns-monitor') {
                loadDnsMonitor();
            }
        });
    });
}

// 載入 DNS 監控器數據
async function loadDnsMonitor() {
    try {
        // 載入統計數據
        const statsResponse = await fetch(`${API_BASE}/nameservers/stats`);
        const stats = await statsResponse.json();
        
        // 更新統計卡片
        let totalDns = 0;
        let healthyDns = 0;
        
        stats.by_country.forEach(item => {
            totalDns += item.total;
            healthyDns += item.healthy;
        });
        
        document.getElementById('dnsTotal').textContent = totalDns;
        document.getElementById('dnsHealthy').textContent = healthyDns;
        document.getElementById('dnsCountries').textContent = stats.by_country.length;
        document.getElementById('dnsIsps').textContent = stats.by_isp.length;
        
        // 創建國家過濾器
        createCountryFilters(stats.by_country);
        
        // 載入 DNS 列表
        const dnsResponse = await fetch(`${API_BASE}/nameservers`);
        allDnsServers = await dnsResponse.json();
        displayDnsServers(allDnsServers);
        
    } catch (error) {
        console.error('載入 DNS 監控器失敗:', error);
        const container = document.getElementById('dnsListContainer');
        if (container) {
            container.innerHTML = '<div class="loading">載入失敗</div>';
        }
    }
}

// 創建國家過濾器
function createCountryFilters(countries) {
    const filtersContainer = document.getElementById('countryFilters');
    
    // 清空現有過濾器（保留"全部"按鈕）
    filtersContainer.innerHTML = '<button class="country-filter-btn active" data-country="all">🌍 全部</button>';
    
    countries.forEach(country => {
        const button = document.createElement('button');
        button.className = 'country-filter-btn';
        button.dataset.country = country.country_code;
        
        const flag = countryFlags[country.country_code] || '🏳️';
        const name = countryNames[country.country_code] || country.country_code;
        
        button.innerHTML = `${flag} ${name} (${country.total})`;
        
        button.addEventListener('click', () => {
            document.querySelectorAll('.country-filter-btn').forEach(btn => 
                btn.classList.remove('active')
            );
            button.classList.add('active');
            currentCountry = country.country_code;
            filterDnsByCountry(country.country_code);
        });
        
        filtersContainer.appendChild(button);
    });
    
    // 為"全部"按鈕添加事件監聽器
    filtersContainer.querySelector('[data-country="all"]').addEventListener('click', () => {
        document.querySelectorAll('.country-filter-btn').forEach(btn => 
            btn.classList.remove('active')
        );
        filtersContainer.querySelector('[data-country="all"]').classList.add('active');
        currentCountry = 'all';
        displayDnsServers(allDnsServers);
    });
}

// 按國家過濾 DNS
function filterDnsByCountry(countryCode) {
    const filtered = allDnsServers.filter(dns => dns.country_code === countryCode);
    displayDnsServers(filtered);
}

// 顯示 DNS 列表
function displayDnsServers(servers) {
    const container = document.getElementById('dnsListContainer');
    
    if (servers.length === 0) {
        container.innerHTML = `
            <div class="loading">
                <div style="font-size: 48px; margin-bottom: 20px;">📡</div>
                <div>沒有 DNS 伺服器</div>
                <div style="font-size: 14px; color: #999; margin-top: 10px;">
                    請先導入 DNS 列表
                </div>
            </div>
        `;
        return;
    }
    
    // 按 ISP 分組
    const groupedByIsp = {};
    servers.forEach(dns => {
        const isp = dns.isp || 'Unknown';
        if (!groupedByIsp[isp]) {
            groupedByIsp[isp] = [];
        }
        groupedByIsp[isp].push(dns);
    });
    
    // 生成 HTML
    let html = '';
    Object.keys(groupedByIsp).sort().forEach(isp => {
        const dnsServers = groupedByIsp[isp];
        const healthyCount = dnsServers.filter(d => d.is_healthy).length;
        
        html += `
            <div class="isp-section">
                <div class="isp-header">
                    <span>${isp}</span>
                    <span class="isp-count">${healthyCount}/${dnsServers.length} 健康</span>
                </div>
                <div class="dns-grid">
                    ${dnsServers.map(dns => createDnsCard(dns)).join('')}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 創建 DNS 卡片
function createDnsCard(dns) {
    const healthClass = dns.is_healthy ? 'healthy' : 'unhealthy';
    const statusBadge = dns.is_healthy ? 
        '<span class="dns-status-badge healthy">✓ 健康</span>' : 
        '<span class="dns-status-badge unhealthy">✗ 異常</span>';
    
    const flag = countryFlags[dns.country_code] || '🏳️';
    const responseTime = dns.response_time_ms ? `${dns.response_time_ms}ms` : '-';
    const lastCheck = dns.last_check ? 
        new Date(dns.last_check).toLocaleString('zh-TW', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }) : '未檢查';
    
    return `
        <div class="dns-card ${healthClass}">
            <div class="dns-ip">${dns.dns_server}</div>
            <div class="dns-info">
                <div class="dns-info-row">
                    <span style="font-weight: 500;">地區:</span>
                    <span>${flag} ${dns.region || '-'}</span>
                </div>
                <div class="dns-info-row">
                    <span style="font-weight: 500;">類型:</span>
                    <span>${getDnsTypeLabel(dns.dns_type)}</span>
                </div>
                <div class="dns-info-row">
                    <span style="font-weight: 500;">回應:</span>
                    <span>${responseTime}</span>
                </div>
                <div class="dns-info-row">
                    <span style="font-weight: 500;">狀態:</span>
                    ${statusBadge}
                </div>
                <div class="dns-info-row">
                    <span style="font-weight: 500;">檢查:</span>
                    <span style="font-size: 11px;">${lastCheck}</span>
                </div>
            </div>
        </div>
    `;
}

// DNS 類型標籤
function getDnsTypeLabel(type) {
    const labels = {
        'international': '🌍 國際',
        'china_isp': '🇨🇳 中國 ISP',
        'regional': '🌏 區域'
    };
    return labels[type] || type || '-';
}

// Setup Domain Test
function setupDomainTest() {
    const testBtn = document.getElementById('testBtn');
    const testInput = document.getElementById('testDomain');
    const testResult = document.getElementById('testResult');

    testBtn.addEventListener('click', async () => {
        const domain = testInput.value.trim();
        if (!domain) {
            alert('請輸入域名');
            return;
        }

        // Show loading
        testBtn.disabled = true;
        testBtn.innerHTML = '<span class="loading-spinner"></span> 測試中...';
        testResult.style.display = 'block';
        testResult.innerHTML = '<div class="loading">正在檢查域名...</div>';

        try {
            const response = await fetch(`${API_BASE}/check/dns`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ domain: domain })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                displayTestResult(domain, data.results);
            } else {
                displayTestError(data.detail || '檢查失敗');
            }
        } catch (error) {
            console.error('Test error:', error);
            displayTestError('網絡錯誤，請稍後再試');
        } finally {
            testBtn.disabled = false;
            testBtn.textContent = '開始測試';
        }
    });

    // Enter key support
    testInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            testBtn.click();
        }
    });
}

// Display Test Result
function displayTestResult(domain, results) {
    const successRate = results.success_rate * 100;
    const totalChecks = results.total_checks;
    const successCount = results.success_count;
    const failedNS = results.failed_nameservers || [];
    const validResolutions = results.valid_resolutions || [];

    let statusClass = 'success';
    let statusText = '✅ 正常';
    let statusIcon = '✅';

    if (successRate === 0) {
        statusClass = 'error';
        statusText = '❌ 失敗';
        statusIcon = '❌';
    } else if (successRate < 50) {
        statusClass = 'warning';
        statusText = '⚠️ 警告';
        statusIcon = '⚠️';
    }

    const resultHTML = `
        <div class="test-result-header">
            <div class="test-result-title">${statusIcon} ${domain}</div>
            <div class="test-result-status ${statusClass}">${statusText}</div>
        </div>
        <div class="test-result-body">
            <div class="test-metric">
                <span class="test-metric-label">檢查時間</span>
                <span class="test-metric-value">${new Date(results.timestamp).toLocaleString('zh-TW')}</span>
            </div>
            <div class="test-metric">
                <span class="test-metric-label">成功率</span>
                <span class="test-metric-value" style="color: ${successRate > 80 ? 'var(--accent-green)' : successRate > 50 ? 'var(--accent-yellow)' : 'var(--accent-red)'}">
                    ${successRate.toFixed(1)}% (${successCount}/${totalChecks})
                </span>
            </div>
            
            ${validResolutions.length > 0 ? `
                <div class="test-metric">
                    <span class="test-metric-label">解析 IP</span>
                    <span class="test-metric-value">${validResolutions[0].resolved_ips.join(', ')}</span>
                </div>
            ` : ''}
            
            <div class="test-dns-list">
                <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">
                    DNS 伺服器檢查結果：
                </div>
                ${generateDNSList(validResolutions, failedNS)}
            </div>
        </div>
    `;

    document.getElementById('testResult').innerHTML = resultHTML;
    
    // Also display summary in alerts section
    displayTestSummary(domain, results, statusClass);
}

// Generate DNS List
function generateDNSList(validResolutions, failedNS) {
    const allServers = new Map();

    // Add successful resolutions
    validResolutions.forEach(res => {
        allServers.set(res.nameserver, {
            status: 'success',
            ips: res.resolved_ips,
            time: res.response_time_ms
        });
    });

    // Add failed resolutions
    failedNS.forEach(ns => {
        allServers.set(ns.nameserver, {
            status: 'failed',
            error: ns.error || ns.reason || 'Unknown error'
        });
    });

    let html = '';
    allServers.forEach((data, server) => {
        if (data.status === 'success') {
            html += `
                <div class="test-dns-item">
                    <span class="test-dns-server">${server}</span>
                    <span class="test-dns-status success">
                        ✅ ${data.ips.join(', ')} (${data.time}ms)
                    </span>
                </div>
            `;
        } else {
            html += `
                <div class="test-dns-item">
                    <span class="test-dns-server">${server}</span>
                    <span class="test-dns-status failed">
                        ❌ ${data.error}
                    </span>
                </div>
            `;
        }
    });

    return html || '<div class="test-error">無檢查結果</div>';
}

// Display Test Error
function displayTestError(message) {
    const errorHTML = `
        <div class="test-error">
            ❌ ${message}
        </div>
    `;
    document.getElementById('testResult').innerHTML = errorHTML;
}

// Display Test Summary in Alerts Section
function displayTestSummary(domain, results, statusClass) {
    const successRate = results.success_rate * 100;
    const totalChecks = results.total_checks;
    const successCount = results.success_count;
    const validResolutions = results.valid_resolutions || [];
    
    let statusIcon = '✅';
    let statusText = '正常';
    if (statusClass === 'error') {
        statusIcon = '❌';
        statusText = '失敗';
    } else if (statusClass === 'warning') {
        statusIcon = '⚠️';
        statusText = '警告';
    }
    
    const summaryHTML = `
        <div class="test-summary-header">
            <div class="test-summary-title">
                ${statusIcon} 最近測試結果：${domain}
            </div>
            <button class="test-summary-close" onclick="document.getElementById('testSummary').style.display='none'">
                ✕
            </button>
        </div>
        <div class="test-summary-body">
            <div class="test-summary-metric">
                <div class="test-summary-metric-label">狀態</div>
                <div class="test-summary-metric-value ${statusClass}">
                    ${statusIcon} ${statusText}
                </div>
            </div>
            <div class="test-summary-metric">
                <div class="test-summary-metric-label">成功率</div>
                <div class="test-summary-metric-value ${statusClass}">
                    ${successRate.toFixed(0)}%
                </div>
                <div class="test-summary-domain">${successCount}/${totalChecks} DNS 成功</div>
            </div>
            ${validResolutions.length > 0 ? `
                <div class="test-summary-metric">
                    <div class="test-summary-metric-label">解析 IP</div>
                    <div class="test-summary-metric-value" style="font-size: 1rem; color: var(--text-primary);">
                        ${validResolutions[0].resolved_ips.join(', ')}
                    </div>
                    <div class="test-summary-domain">回應時間: ${validResolutions[0].response_time_ms}ms</div>
                </div>
            ` : `
                <div class="test-summary-metric">
                    <div class="test-summary-metric-label">解析 IP</div>
                    <div class="test-summary-metric-value error">
                        無法解析
                    </div>
                    <div class="test-summary-domain">所有 DNS 失敗</div>
                </div>
            `}
            <div class="test-summary-metric">
                <div class="test-summary-metric-label">檢查時間</div>
                <div class="test-summary-metric-value" style="font-size: 0.875rem; color: var(--text-primary);">
                    ${new Date(results.timestamp).toLocaleTimeString('zh-TW')}
                </div>
                <div class="test-summary-domain">${new Date(results.timestamp).toLocaleDateString('zh-TW')}</div>
            </div>
        </div>
    `;
    
    const summaryElement = document.getElementById('testSummary');
    summaryElement.innerHTML = summaryHTML;
    summaryElement.style.display = 'block';
    
    // Scroll to summary
    summaryElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

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

        container.innerHTML = filteredAlerts.map(alert => {
            // 優先使用後端生成的摘要，否則前端生成
            const evidenceSummary = alert.evidence_summary || generateEvidenceSummary(alert);
            
            return `
            <div class="alert-item ${alert.alert_level}">
                <div class="alert-header">
                    <span class="alert-domain">${alert.domain_name || `Domain #${alert.domain_id}`}</span>
                    <span class="alert-badge ${alert.alert_level}">${alert.alert_level}</span>
                </div>
                <div class="alert-cause">
                    ${getRootCauseText(alert.root_cause)}
                </div>
                    ${evidenceSummary ? `<div class="alert-evidence">${evidenceSummary}</div>` : ''}
                <div class="alert-time">
                    首次發現: ${formatTime(alert.first_seen)} | 
                    最後更新: ${formatTime(alert.last_seen)}
                </div>
            </div>
            `;
        }).join('');

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
                        <div class="event-domain">${event.domain_name || `Domain #${event.domain_id}`}</div>
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
function generateEvidenceSummary(alert) {
    if (!alert.evidence) return '';
    
    const evidence = alert.evidence;
    let summary = [];
    
    // 根據不同的根因顯示不同的摘要
    if (alert.root_cause === 'config_error') {
        // DNS 配置錯誤
        const details = evidence.details || evidence.isp_dns?.details || {};
        const failedNS = evidence.failed_nameservers || details.failed_nameservers || [];
        const successRate = evidence.success_rate !== undefined ? evidence.success_rate : 
                           (details.success_rate !== undefined ? details.success_rate : null);
        
        if (failedNS.length > 0) {
            const failedServers = failedNS.slice(0, 3).map(ns => {
                const server = ns.nameserver || 'Unknown';
                const error = ns.error || ns.reason || '';
                if (error.includes('Could not contact DNS servers') || error.includes('NXDOMAIN')) {
                    return `${server}: 無法解析`;
                } else if (error.includes('IP not in whitelist')) {
                    return `${server}: IP 不在白名單`;
                } else if (error) {
                    return `${server}: ${error.substring(0, 20)}`;
                } else {
                    return `${server}: 失敗`;
                }
            });
            
            summary.push(`❌ ${failedServers.join(', ')}`);
            if (failedNS.length > 3) {
                summary.push(`及其他 ${failedNS.length - 3} 個`);
            }
        }
        
        if (successRate !== null && successRate !== undefined) {
            summary.push(`成功率: ${(successRate * 100).toFixed(0)}%`);
        }
    } else if (alert.root_cause === 'domain_hijacked') {
        // 域名劫持
        const oldNS = evidence.old_ns || [];
        const newNS = evidence.new_ns || [];
        
        if (oldNS.length > 0 && newNS.length > 0) {
            summary.push(`🚨 NS 已變更`);
            summary.push(`舊: ${oldNS.slice(0, 2).join(', ')}`);
            summary.push(`新: ${newNS.slice(0, 2).join(', ')}`);
        }
    } else if (alert.root_cause === 'isp_blocked') {
        // ISP 封鎖
        const failedISPs = evidence.failed_isps || [];
        const successRate = evidence.success_rate || 0;
        
        if (failedISPs.length > 0) {
            const ispNames = failedISPs.slice(0, 3).map(isp => isp.nameserver || isp.isp_name).join(', ');
            summary.push(`⚠️ 受影響 ISP: ${ispNames}`);
        }
        summary.push(`成功率: ${(successRate * 100).toFixed(0)}%`);
    } else if (alert.root_cause === 'content_defacement') {
        // 內容竄改
        const keyword = evidence.keyword_expected;
        const httpStatus = evidence.http_status;
        
        if (keyword) {
            summary.push(`⚠️ 關鍵字 "${keyword}" 未找到`);
        }
        if (httpStatus) {
            summary.push(`HTTP 狀態: ${httpStatus}`);
        }
    }
    
    // 如果沒有生成任何摘要，顯示通用信息
    if (summary.length === 0 && alert.root_cause === 'config_error') {
        summary.push('DNS 解析失敗，請檢查域名配置');
    }
    
    return summary.length > 0 ? summary.join(' • ') : '';
}

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

