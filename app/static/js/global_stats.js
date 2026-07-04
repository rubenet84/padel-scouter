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

// ── URL State Persistence ──────────────────────────────────────
function stateToParams() {
    const p = new URLSearchParams();
    if (rankingState.sortBy !== 'points') p.set('sort', rankingState.sortBy);
    if (rankingState.order !== 'desc') p.set('order', rankingState.order);
    if (rankingState.page > 1) p.set('page', String(rankingState.page));
    ['category', 'season', 'competition_type', 'date_from', 'date_to'].forEach(k => {
        const v = rankingState.filters[k];
        if (v) p.set(k, v);
    });
    return p;
}

function syncUrl() {
    const p = stateToParams();
    const qs = p.toString();
    const url = qs ? window.location.pathname + '?' + qs : window.location.pathname;
    history.replaceState(null, '', url);
}

function readStateFromUrl() {
    const p = new URLSearchParams(window.location.search);
    const state = {
        sortBy: 'points',
        order: 'desc',
        page: 1,
        pageSize: 50,
        loaded: false,
        filters: { category: '', season: '', competition_type: '', date_from: '', date_to: '' },
    };
    const sortKey = p.get('sort');
    const validSorts = ['points', 'wins', 'win_pct', 'matches', 'sets_won', 'games_won', 'streak', 'name'];
    if (sortKey && validSorts.includes(sortKey)) state.sortBy = sortKey;
    const order = p.get('order');
    if (order === 'asc' || order === 'desc') state.order = order;
    const page = parseInt(p.get('page'), 10);
    if (page > 1) state.page = page;
    ['category', 'season', 'competition_type', 'date_from', 'date_to'].forEach(k => {
        const v = p.get(k);
        if (v) state.filters[k] = v;
    });
    return state;
}

function applyFiltersToDom() {
    const f = rankingState.filters;
    const el = document.getElementById('filter-category');
    if (el && f.category) el.value = f.category;
    const el2 = document.getElementById('filter-season');
    if (el2 && f.season) el2.value = f.season;
    const el3 = document.getElementById('filter-type');
    if (el3 && f.competition_type) el3.value = f.competition_type;
    const el4 = document.getElementById('filter-date-from');
    if (el4 && f.date_from) el4.value = f.date_from;
    const el5 = document.getElementById('filter-date-to');
    if (el5 && f.date_to) el5.value = f.date_to;
}

// ── Ranking State (mutable, persisted via URL) ──────────────────
let rankingState = readStateFromUrl();

function getFilterValues() {
    return {
        category: document.getElementById('filter-category')?.value || '',
        season: document.getElementById('filter-season')?.value || '',
        competition_type: document.getElementById('filter-type')?.value || '',
        date_from: document.getElementById('filter-date-from')?.value || '',
        date_to: document.getElementById('filter-date-to')?.value || '',
    };
}

function buildRankingUrl() {
    Object.assign(rankingState.filters, getFilterValues());
    const params = new URLSearchParams();
    params.set('sort_by', rankingState.sortBy);
    params.set('order', rankingState.order);
    params.set('page', String(rankingState.page));
    params.set('page_size', String(rankingState.pageSize));
    const f = rankingState.filters;
    if (f.category) params.set('category', f.category);
    if (f.season) params.set('season', f.season);
    if (f.competition_type) params.set('competition_type', f.competition_type);
    if (f.date_from) params.set('date_from', f.date_from);
    if (f.date_to) params.set('date_to', f.date_to);
    return `/api/v1/stats/ranking?${params.toString()}`;
}

// ── Summary ─────────────────────────────────────────────────────
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

// ── Ranking ─────────────────────────────────────────────────────
async function loadRanking() {
    const tbody = document.getElementById('ranking-body');
    if (!tbody) return;

    if (!TOKEN) {
        tbody.innerHTML = '<tr><td colspan="10" class="p-6 text-center text-gray-500">Inicia sesión para ver el ranking</td></tr>';
        return;
    }

    tbody.innerHTML = '<tr><td colspan="10" class="p-6 text-center text-gray-500"><span class="animate-pulse">Cargando ranking...</span></td></tr>';

    const url = buildRankingUrl();

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) {
            tbody.innerHTML = '<tr><td colspan="10" class="p-6 text-center text-red-400">Error al cargar el ranking</td></tr>';
            return;
        }
        const json = await res.json();
        if (!json.success) {
            tbody.innerHTML = `<tr><td colspan="10" class="p-6 text-center text-red-400">${escHtml(json.error || 'Error desconocido')}</td></tr>`;
            return;
        }
        renderRanking(json.data);
        syncUrl(); // persist URL state
    } catch {
        tbody.innerHTML = '<tr><td colspan="10" class="p-6 text-center text-red-400">Error de conexión</td></tr>';
    }
}

function medalIcon(position) {
    if (position === 1) return '<span class="text-lg" title="Oro">🥇</span>';
    if (position === 2) return '<span class="text-lg" title="Plata">🥈</span>';
    if (position === 3) return '<span class="text-lg" title="Bronce">🥉</span>';
    return '';
}

function streakDisplay(streak) {
    if (streak === 0) return '<span class="text-gray-500">—</span>';
    if (streak > 0) return `<span class="text-emerald-400 font-bold">W${streak}</span>`;
    return `<span class="text-red-400 font-bold">L${Math.abs(streak)}</span>`;
}

function renderRanking(data) {
    const tbody = document.getElementById('ranking-body');
    if (!tbody) return;

    const players = data.players || [];

    if (players.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="p-6 text-center text-gray-500">Sin datos de ranking</td></tr>';
    } else {
        tbody.innerHTML = players.map(p => {
            const medal = medalIcon(p.position);
            const streak = streakDisplay(p.streak);
            return `
                <tr class="border-b border-[#2A2A3A] hover:bg-white/5 transition-colors">
                    <td class="p-3 text-center text-gray-400 font-mono text-xs">${p.position}</td>
                    <td class="p-3">
                        <div class="flex items-center gap-2">
                            ${medal}
                            <a href="/player/${p.id}" class="text-white font-medium hover:text-emerald-400 transition-colors">${escHtml(p.name)}</a>
                        </div>
                    </td>
                    <td class="p-3 text-gray-400 text-xs">${escHtml(p.category)}</td>
                    <td class="p-3 text-right text-white font-semibold font-mono">${p.points}</td>
                    <td class="p-3 text-right text-white font-mono">${p.wins}</td>
                    <td class="p-3 text-right text-white font-mono">${p.win_pct}%</td>
                    <td class="p-3 text-right text-gray-400 font-mono">${p.matches}</td>
                    <td class="p-3 text-right text-white font-mono">${p.sets_won}</td>
                    <td class="p-3 text-right text-white font-mono">${p.games_won}</td>
                    <td class="p-3 text-right">${streak}</td>
                </tr>
            `;
        }).join('');
    }

    // Update sort icons + active column highlight
    updateSortIcons();

    // Render pagination
    renderPagination(data);
}

function updateSortIcons() {
    document.querySelectorAll('#ranking-table .sortable').forEach(th => {
        const icon = th.querySelector('.sort-icon');
        if (!icon) return;
        const sortKey = th.dataset.sort;
        if (sortKey === rankingState.sortBy) {
            // Active column: highlight the header text + show arrow
            th.classList.add('text-emerald-400');
            icon.textContent = rankingState.order === 'asc' ? ' ▲' : ' ▼';
        } else {
            // Inactive: dimmed, no arrow
            th.classList.remove('text-emerald-400');
            icon.textContent = '';
        }
    });
}

function renderPagination(data) {
    const container = document.getElementById('ranking-pagination');
    if (!container) return;

    if (data.total_pages <= 1) {
        container.classList.add('hidden');
        container.innerHTML = '';
        return;
    }

    container.classList.remove('hidden');

    const current = data.page;
    const total = data.total_pages;
    const pages = [];

    // Previous
    pages.push(`<button class="px-3 py-1 rounded-lg text-sm font-medium transition-colors ${current === 1 ? 'text-gray-600 cursor-not-allowed' : 'text-white hover:bg-white/10'}" data-page="${current - 1}" ${current === 1 ? 'disabled' : ''}>‹</button>`);

    // Page numbers
    const maxVisible = 5;
    let start = Math.max(1, current - Math.floor(maxVisible / 2));
    let end = Math.min(total, start + maxVisible - 1);
    if (end - start + 1 < maxVisible) {
        start = Math.max(1, end - maxVisible + 1);
    }

    if (start > 1) {
        pages.push(`<button class="px-3 py-1 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/10 transition-colors" data-page="1">1</button>`);
        if (start > 2) pages.push(`<span class="px-1 text-gray-600">…</span>`);
    }

    for (let i = start; i <= end; i++) {
        const active = i === current ? 'bg-emerald-600 text-white font-bold' : 'text-gray-400 hover:text-white hover:bg-white/10';
        pages.push(`<button class="px-3 py-1 rounded-lg text-sm font-medium transition-colors ${active}" data-page="${i}">${i}</button>`);
    }

    if (end < total) {
        if (end < total - 1) pages.push(`<span class="px-1 text-gray-600">…</span>`);
        pages.push(`<button class="px-3 py-1 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/10 transition-colors" data-page="${total}">${total}</button>`);
    }

    // Next
    pages.push(`<button class="px-3 py-1 rounded-lg text-sm font-medium transition-colors ${current === total ? 'text-gray-600 cursor-not-allowed' : 'text-white hover:bg-white/10'}" data-page="${current + 1}" ${current === total ? 'disabled' : ''}>›</button>`);

    container.innerHTML = pages.join('');

    // Click handlers
    container.querySelectorAll('button[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            const p = parseInt(btn.dataset.page, 10);
            if (p && p !== rankingState.page) {
                rankingState.page = p;
                loadRanking();
            }
        });
    });
}

// ── Sort Handlers ──────────────────────────────────────────────
function initSortHandlers() {
    document.querySelectorAll('#ranking-table .sortable').forEach(th => {
        th.addEventListener('click', () => {
            const sortKey = th.dataset.sort;
            if (!sortKey) return;

            if (rankingState.sortBy === sortKey) {
                // Toggle order
                rankingState.order = rankingState.order === 'asc' ? 'desc' : 'asc';
            } else {
                rankingState.sortBy = sortKey;
                // Default order: desc for most, asc for name
                const defaultOrders = {
                    points: 'desc', wins: 'desc', win_pct: 'desc',
                    matches: 'desc', sets_won: 'desc', games_won: 'desc',
                    streak: 'desc', name: 'asc',
                };
                rankingState.order = defaultOrders[sortKey] || 'desc';
            }
            rankingState.page = 1;
            loadRanking();
        });
    });
}

// ── Filter Apply ───────────────────────────────────────────────
function initFilterHandlers() {
    const applyBtn = document.getElementById('filter-apply');
    if (!applyBtn) return;

    applyBtn.addEventListener('click', () => {
        rankingState.page = 1;
        loadRanking();
    });

    // Also apply on Enter key in date inputs
    ['filter-date-from', 'filter-date-to'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    rankingState.page = 1;
                    loadRanking();
                }
            });
        }
    });
}

// ── Lazy Load Ranking (IntersectionObserver) ──────────────────
function initRankingLazyLoad() {
    const section = document.getElementById('ranking-container');
    if (!section) return;

    // If URL has state params, don't wait for scroll — load immediately
    const hasUrlState = !!window.location.search;

    const doLoad = () => {
        rankingState.loaded = true;
        loadRanking();
        initSortHandlers();
        initFilterHandlers();
    };

    if (hasUrlState) {
        applyFiltersToDom();
        doLoad();
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !rankingState.loaded) {
                doLoad();
                observer.disconnect();
            }
        });
    }, { rootMargin: '200px' });

    observer.observe(section);
}

// ── Init ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadSummary();
    initRankingLazyLoad();
});
