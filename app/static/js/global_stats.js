// ── Global Stats Dashboard ──────────────────────────────────────
const TOKEN = localStorage.getItem('access_token');

function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function showError(container, msg) {
    if (!container) return;
    container.innerHTML = `<div class="col-span-full text-center text-gray-500 py-12">${escHtml(msg)}</div>`;
}

async function loadSummary() {
    const container = document.getElementById('dashboard-summary');
    if (!container) return;

    if (!TOKEN) {
        showError(container, 'Inicia sesión para ver estadísticas');
        return;
    }

    try {
        const res = await fetch('/api/v1/stats/summary', {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) {
            showError(container, 'No se pudieron cargar las estadísticas');
            return;
        }
        const json = await res.json();
        if (!json.success) {
            showError(container, json.error || 'Error al cargar estadísticas');
            return;
        }
        renderSummary(json.data);
    } catch {
        showError(container, 'Error de conexión al cargar estadísticas');
    }
}

function renderSummary(data) {
    const container = document.getElementById('dashboard-summary');
    if (!container) return;

    const cards = [
        { label: 'Jugadores', value: data.total_players, color: '#00B4D8', icon: '🎾' },
        { label: 'Partidos', value: data.total_matches, color: '#a855f7', icon: '⚔️' },
        { label: 'Torneos', value: data.total_tournaments, color: '#FF6B00', icon: '🏆' },
        { label: 'Amistosos', value: data.total_friendlies, color: '#10b981', icon: '🤝' },
        { label: 'Sets', value: data.total_sets, color: '#f59e0b', icon: '📊' },
        { label: 'Juegos', value: data.total_games, color: '#ef4444', icon: '🎯' },
    ];

    container.innerHTML = `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4" id="summary-cards">
            ${cards.map(c => `
                <div class="gradient-border rounded-2xl card-hover" style="background:#12121A;" role="region" aria-label="${escHtml(c.label)}">
                    <div class="p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <span aria-hidden="true">${c.icon}</span>
                            <span class="text-xs font-bold uppercase tracking-widest" style="color:${c.color};">${escHtml(c.label)}</span>
                        </div>
                        <div class="text-2xl font-black text-white" aria-label="${c.value}">${c.value}</div>
                    </div>
                </div>
            `).join('')}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div class="gradient-border rounded-2xl card-hover" style="background:#12121A;" role="region" aria-label="Líder del Ranking">
                <div class="p-4">
                    <div class="flex items-center gap-2 mb-2">
                        <span aria-hidden="true">👑</span>
                        <span class="text-xs font-bold uppercase tracking-widest" style="color:#FFD700;">Líder del Ranking</span>
                    </div>
                    ${data.ranking_leader
                        ? `<a href="/player/${data.ranking_leader.id}" class="text-lg font-bold text-white hover:text-emerald-400 transition-colors">${escHtml(data.ranking_leader.name)}</a>
                           <div class="text-sm text-gray-400 mt-1">${data.ranking_leader.points} pts · ${data.ranking_leader.category}</div>`
                        : '<div class="text-gray-500">Sin datos</div>'}
                </div>
            </div>
            <div class="gradient-border rounded-2xl card-hover" style="background:#12121A;" role="region" aria-label="Mejor porcentaje de victorias">
                <div class="p-4">
                    <div class="flex items-center gap-2 mb-2">
                        <span aria-hidden="true">⭐</span>
                        <span class="text-xs font-bold uppercase tracking-widest" style="color:#00FF87;">Mejor % de Victorias</span>
                    </div>
                    ${data.best_win_pct
                        ? `<a href="/player/${data.best_win_pct.id}" class="text-lg font-bold text-white hover:text-emerald-400 transition-colors">${escHtml(data.best_win_pct.name)}</a>
                           <div class="text-sm text-gray-400 mt-1">${data.best_win_pct.win_pct}% · ${data.best_win_pct.category}</div>`
                        : '<div class="text-gray-500">Sin datos</div>'}
                </div>
            </div>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', loadSummary);
