export function init() {
    if (typeof Chart === 'undefined') {
        document.querySelectorAll('[data-chart]').forEach(el => {
            // outerHTML replaces the canvas element itself so fallback text is
            // visible even when canvas is supported (innerHTML on a <canvas>
            // only shows as fallback when canvas is unsupported).
            el.outerHTML = '<div class="landing-chart-fallback">Gráfico no disponible</div>';
        });
        return;
    }

    const dataEl = document.getElementById('landing-data');
    if (!dataEl) return;

    let data;
    try {
        data = JSON.parse(dataEl.textContent);
    } catch(e) {
        return;
    }

    const analytics = data.analytics;
    if (!analytics) return;

    // Dark theme defaults
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';

    // Radar chart
    const radarCtx = document.getElementById('landing-radar-chart');
    if (radarCtx && analytics.radar_labels) {
        new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: analytics.radar_labels,
                datasets: [{
                    label: 'Tus stats',
                    data: analytics.radar_data,
                    backgroundColor: 'rgba(0,255,135,0.1)',
                    borderColor: '#00FF87',
                    borderWidth: 2,
                    pointBackgroundColor: '#00FF87',
                    pointBorderColor: '#0A0A0F',
                    pointBorderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // Donut chart
    const donutCtx = document.getElementById('landing-donut-chart');
    if (donutCtx && analytics.win_rate !== undefined) {
        new Chart(donutCtx, {
            type: 'doughnut',
            data: {
                labels: ['Victorias', 'Derrotas'],
                datasets: [{
                    data: [analytics.win_rate, 100 - analytics.win_rate],
                    backgroundColor: ['#00FF87', 'rgba(255,255,255,0.05)'],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                cutout: '75%',
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}
