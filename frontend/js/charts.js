/**
 * Chart.js Equity Curve Rendering
 */

let equityChart = null;

/**
 * Initialize the equity curve chart
 */
async function initEquityChart() {
    try {
        // Fetch equity curve data from API
        const response = await fetch('/api/equity_curve?days=30');
        const data = await response.json();

        // Get canvas context
        const ctx = document.getElementById('equity-chart');
        if (!ctx) {
            console.error('Canvas element not found');
            return;
        }

        // Create Chart.js instance
        equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates || [],
                datasets: [{
                    label: '账户权益 (USD)',
                    data: data.equity || [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#10b981',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#e2e8f0',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return '权益: $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#1e293b',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            maxTicksLimit: 8,
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#1e293b',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                }
            }
        });

        console.log('Equity chart initialized');
    } catch (error) {
        console.error('Error initializing equity chart:', error);
    }
}

/**
 * Update the equity chart with new data
 */
function updateEquityChart(newData) {
    if (!equityChart) {
        console.warn('Chart not initialized yet');
        return;
    }

    try {
        equityChart.data.labels = newData.dates || [];
        equityChart.data.datasets[0].data = newData.equity || [];
        equityChart.update('none'); // Update without animation for smoother updates
        console.log('Equity chart updated');
    } catch (error) {
        console.error('Error updating equity chart:', error);
    }
}

/**
 * Refresh equity chart data from API
 */
async function refreshEquityChart() {
    try {
        const response = await fetch('/api/equity_curve?days=30');
        const data = await response.json();
        updateEquityChart(data);
    } catch (error) {
        console.error('Error refreshing equity chart:', error);
    }
}

/**
 * Destroy and recreate the chart (useful for hard refresh)
 */
async function recreateEquityChart() {
    if (equityChart) {
        equityChart.destroy();
        equityChart = null;
    }
    await initEquityChart();
}
