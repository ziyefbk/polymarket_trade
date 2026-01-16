/**
 * Main Dashboard Logic
 */

// =========================================================================
// Initialization
// =========================================================================

/**
 * Initialize the dashboard on page load
 */
async function initDashboard() {
    try {
        console.log('Initializing dashboard...');

        // Load initial data from API
        await loadInitialData();

        // Initialize equity chart
        await initEquityChart();

        // Load recent trades
        await loadRecentTrades();

        // Load open positions
        await loadOpenPositions();

        console.log('✓ Dashboard initialized successfully');
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

/**
 * Load initial data from API endpoints
 */
async function loadInitialData() {
    try {
        const [status, metrics] = await Promise.all([
            fetch('/api/status').then(r => r.json()),
            fetch('/api/performance').then(r => r.json())
        ]);

        updateDashboard(status, metrics);
    } catch (error) {
        console.error('Error loading initial data:', error);
        throw error;
    }
}

// =========================================================================
// Dashboard Updates
// =========================================================================

/**
 * Update all dashboard elements with new data
 */
function updateDashboard(status, metrics) {
    // Update status bar
    if (status) {
        updateStatusBar(status);
    }

    // Update metric cards
    if (metrics) {
        updateMetricCards(metrics);
        updateDetailsSection(metrics);
    }
}

/**
 * Update status bar (uptime, etc.)
 */
function updateStatusBar(status) {
    const uptimeElement = document.getElementById('uptime');
    if (uptimeElement && status.uptime) {
        uptimeElement.textContent = `运行时间: ${status.uptime}`;
    }

    // Update opportunities and trades count
    const opportunitiesToday = document.getElementById('opportunities-today');
    const tradesToday = document.getElementById('trades-today');

    if (opportunitiesToday && status.opportunities_found_today !== undefined) {
        opportunitiesToday.textContent = `机会: ${status.opportunities_found_today}`;
    }

    if (tradesToday && status.trades_executed_today !== undefined) {
        tradesToday.textContent = status.trades_executed_today;
    }
}

/**
 * Update metric cards
 */
function updateMetricCards(metrics) {
    // Daily profit
    const dailyProfit = document.getElementById('daily-profit');
    if (dailyProfit && metrics.net_profit !== undefined) {
        const profit = metrics.net_profit || 0;
        dailyProfit.textContent = formatCurrency(profit);

        // Update profit change indicator
        const profitChange = document.getElementById('daily-profit-change');
        if (profitChange) {
            if (profit >= 0) {
                profitChange.textContent = `+${formatPercent(profit / 1000)}`; // Assuming base of 1000
                profitChange.className = 'metric-change positive';
            } else {
                profitChange.textContent = formatPercent(profit / 1000);
                profitChange.className = 'metric-change negative';
            }
        }
    }

    // Win rate
    const winRate = document.getElementById('win-rate');
    if (winRate && metrics.win_rate !== undefined) {
        winRate.textContent = formatPercent(metrics.win_rate);
    }

    const winRateSubtitle = document.getElementById('win-rate-subtitle');
    if (winRateSubtitle && metrics.total_trades !== undefined) {
        const successfulTrades = Math.round(metrics.total_trades * (metrics.win_rate || 0));
        winRateSubtitle.textContent = `${successfulTrades}/${metrics.total_trades} 成功`;
    }

    // Trades today (already updated in status bar)
    // Open positions will be updated separately
}

/**
 * Update details section
 */
function updateDetailsSection(metrics) {
    // Total profit
    const totalProfit = document.getElementById('total-profit');
    if (totalProfit && metrics.net_profit !== undefined) {
        totalProfit.textContent = formatCurrency(metrics.net_profit);
    }

    // Sharpe ratio
    const sharpeRatio = document.getElementById('sharpe-ratio');
    if (sharpeRatio && metrics.sharpe_ratio !== undefined) {
        sharpeRatio.textContent = metrics.sharpe_ratio > 0
            ? metrics.sharpe_ratio.toFixed(2)
            : 'N/A';
    }

    // Max drawdown
    const maxDrawdown = document.getElementById('max-drawdown');
    if (maxDrawdown && metrics.max_drawdown !== undefined) {
        maxDrawdown.textContent = formatPercent(metrics.max_drawdown);
    }

    // Average profit per trade
    const avgProfit = document.getElementById('avg-profit');
    if (avgProfit && metrics.avg_profit_per_trade !== undefined) {
        avgProfit.textContent = formatCurrency(metrics.avg_profit_per_trade);
    }
}

/**
 * Update status indicator badge
 */
function updateStatusIndicator(status) {
    const statusBadge = document.getElementById('bot-status');
    if (!statusBadge) return;

    statusBadge.className = `status-badge ${status}`;

    const statusText = {
        'running': '运行中',
        'disconnected': '已断开',
        'error': '错误'
    };

    statusBadge.textContent = statusText[status] || status;
}

// =========================================================================
// Trades Management
// =========================================================================

/**
 * Load recent trades from API
 */
async function loadRecentTrades() {
    try {
        const trades = await fetch('/api/trades/recent?limit=10').then(r => r.json());
        const tradesList = document.getElementById('trades-list');

        if (!tradesList) return;

        if (trades.length === 0) {
            tradesList.innerHTML = '<div class="no-data">暂无交易记录</div>';
            return;
        }

        // Clear existing trades
        tradesList.innerHTML = '';

        // Add each trade
        trades.forEach(trade => addTradeToList(trade, false));
    } catch (error) {
        console.error('Error loading recent trades:', error);
    }
}

/**
 * Add a single trade to the list
 */
function addTradeToList(trade, animate = true) {
    const tradesList = document.getElementById('trades-list');
    if (!tradesList) return;

    // Remove "no data" message if present
    const noData = tradesList.querySelector('.no-data');
    if (noData) {
        noData.remove();
    }

    // Create trade element
    const tradeElement = document.createElement('div');
    tradeElement.className = `trade-item ${trade.status || 'OPEN'}`;

    const profitClass = (trade.actual_profit || 0) >= 0 ? 'positive' : 'negative';
    const profitSign = (trade.actual_profit || 0) >= 0 ? '+' : '';

    tradeElement.innerHTML = `
        <div class="trade-header">
            <span class="trade-title">${escapeHtml(trade.event_title || 'Unknown Event')}</span>
            <span class="trade-profit ${profitClass}">
                ${profitSign}${formatCurrency(trade.actual_profit || 0)}
            </span>
        </div>
        <div class="trade-meta">
            <span class="trade-type">${escapeHtml(trade.arbitrage_type || 'N/A')}</span>
            <span class="trade-time">${formatTime(trade.executed_at)}</span>
        </div>
    `;

    // Insert at the top (most recent first)
    tradesList.insertBefore(tradeElement, tradesList.firstChild);

    // Limit to 10 trades
    while (tradesList.children.length > 10) {
        tradesList.removeChild(tradesList.lastChild);
    }

    // Play animation
    if (animate) {
        tradeElement.style.animation = 'slideIn 0.3s ease';
    }
}

// =========================================================================
// Positions Management
// =========================================================================

/**
 * Load open positions from API
 */
async function loadOpenPositions() {
    try {
        const positions = await fetch('/api/positions/open').then(r => r.json());

        const openPositionsCount = document.getElementById('open-positions');
        const openPositionsCapital = document.getElementById('open-positions-capital');

        if (openPositionsCount) {
            openPositionsCount.textContent = positions.length;
        }

        if (openPositionsCapital) {
            const totalCapital = positions.reduce((sum, p) => sum + (p.size * p.entry_price || 0), 0);
            openPositionsCapital.textContent = `${formatCurrency(totalCapital)} 资金`;
        }
    } catch (error) {
        console.error('Error loading open positions:', error);
    }
}

// =========================================================================
// Utility Functions
// =========================================================================

/**
 * Format currency value
 */
function formatCurrency(value) {
    return '$' + (value || 0).toFixed(2);
}

/**
 * Format percentage value
 */
function formatPercent(value) {
    return ((value || 0) * 100).toFixed(1) + '%';
}

/**
 * Format timestamp to relative time
 */
function formatTime(isoString) {
    if (!isoString) return 'N/A';

    try {
        const date = new Date(isoString);
        const now = new Date();
        const diff = now - date;

        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}天前`;
        if (hours > 0) return `${hours}小时前`;
        if (minutes > 0) return `${minutes}分钟前`;
        return `${seconds}秒前`;
    } catch (error) {
        return 'N/A';
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show error message
 */
function showError(message) {
    console.error(message);
    // Could show a toast notification here
}

// =========================================================================
// Page Load
// =========================================================================

// Initialize dashboard when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

// Refresh data periodically (every 30 seconds)
setInterval(async () => {
    try {
        await loadInitialData();
        await refreshEquityChart();
        await loadOpenPositions();
    } catch (error) {
        console.error('Error during periodic refresh:', error);
    }
}, 30000);
