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
    history.replaceState(null, '', url + window.location.hash);
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
                <div class="rounded-xl border border-[#2A2A3A] card-hover" style="background:#12121A;" role="region" aria-label="${escHtml(c.label)}">
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
            <div class="rounded-xl border border-[#2A2A3A] card-hover" style="background:#12121A;" role="region" aria-label="Líder del Ranking">
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
            <div class="rounded-xl border border-[#2A2A3A] card-hover" style="background:#12121A;" role="region" aria-label="Mejor porcentaje de victorias">
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
        // Si hay hash, scrollear después de renderizar (el contenido asíncrono desplaza)
        if (window.location.hash) {
          const targets = { '#ranking-title': 'ranking-container', '#ranking-container': 'ranking-container', '#top-section': 'top-section', '#compare-section': 'compare-section', '#records-section': 'records-section' };
          const id = targets[window.location.hash];
          const el = id && document.getElementById(id);
          if (el) {
            setTimeout(() => {
              const rect = el.getBoundingClientRect();
              window.scrollTo({ top: window.scrollY + rect.top - 64, behavior: 'instant' });
            }, 250);
          }
        }
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
        // Also reload top players with new filters
        loadTopPlayers();
        // PR #4: Reload new sections with new filters
        loadRecords();
        loadCategoryStats();
        loadEvolution();
        loadCommunityHighlights();
    });

    // Also apply on Enter key in date inputs
    ['filter-date-from', 'filter-date-to'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    rankingState.page = 1;
                    loadRanking();
                    loadTopPlayers();
                    // PR #4: Reload new sections
                    loadRecords();
                    loadCategoryStats();
                    loadEvolution();
                    loadCommunityHighlights();
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

// ── Top Players ──────────────────────────────────────────────────
const TOP_METRICS = [
    { key: 'top_points',            label: 'Puntos FEP',        icon: '🏆', color: '#FFD700' },
    { key: 'top_wins',             label: 'Victorias',         icon: '✅', color: '#10b981' },
    { key: 'top_win_pct',          label: '% Victorias',       icon: '🎯', color: '#00B4D8' },
    { key: 'top_matches',          label: 'Partidos Jugados',  icon: '⚔️', color: '#a855f7' },
    { key: 'top_tournaments_won',  label: 'Torneos Ganados',   icon: '🏅', color: '#FF6B00' },
    { key: 'top_finals',           label: 'Finales',           icon: '🏁', color: '#ef4444' },
    { key: 'top_semis',            label: 'Semifinales',        icon: '🔶', color: '#f59e0b' },
    { key: 'top_sets_won',         label: 'Sets Ganados',      icon: '📊', color: '#6366f1' },
    { key: 'top_games_won',        label: 'Juegos Ganados',    icon: '🎾', color: '#ec4899' },
    { key: 'top_streak',           label: 'Racha Actual',      icon: '🔥', color: '#f97316' },
];

const TOP_POSITIONS = ['🥇', '🥈', '🥉', '4.', '5.'];

async function loadTopPlayers() {
    const section = document.getElementById('top-section');
    if (!section) return;

    if (!TOKEN) {
        section.classList.add('hidden');
        return;
    }

    const params = buildFilterParams();
    const url = `/api/v1/stats/top?${params.toString()}`;

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) return;
        const json = await res.json();
        if (!json.success) return;
        renderTopPlayers(json.data);
    } catch {
        // silently fail
    }
}

function renderTopPlayers(data) {
    const section = document.getElementById('top-section');
    const grid = document.getElementById('top-grid');
    if (!grid) return;
    if (section) section.classList.remove('hidden');

    grid.innerHTML = TOP_METRICS.map(metric => {
        const entries = data[metric.key] || [];
        return `
            <div class="rounded-xl border border-[#2A2A3A] p-4" style="background:#12121A;">
                <div class="flex items-center gap-2 mb-3">
                    <span aria-hidden="true">${metric.icon}</span>
                    <span class="text-sm font-bold uppercase tracking-widest" style="color:${metric.color};">${escHtml(metric.label)}</span>
                </div>
                <div class="space-y-1.5">
                    ${entries.length === 0
                        ? '<div class="text-gray-500 text-sm py-2">Sin datos</div>'
                        : entries.map((e, i) => `
                            <div class="flex items-center justify-between text-sm">
                                <div class="flex items-center gap-2 min-w-0">
                                    <span class="text-xs font-mono shrink-0" style="color:${metric.color};">${TOP_POSITIONS[i] || (i + 1) + '.'}</span>
                                    <a href="/player/${e.player_id}" class="text-white hover:text-emerald-400 transition-colors truncate">${escHtml(e.name)}</a>
                                    <span class="text-xs text-gray-500 shrink-0">${escHtml(e.category)}</span>
                                </div>
                                <span class="text-white font-semibold font-mono ml-2 shrink-0">${e.value}</span>
                            </div>
                        `).join('')
                    }
                </div>
            </div>
        `;
    }).join('');
}

// ── Helper: build filter params from current state ──────────────
function buildFilterParams() {
    const f = getFilterValues();
    const p = new URLSearchParams();
    if (f.category) p.set('category', f.category);
    if (f.season) p.set('season', f.season);
    if (f.competition_type) p.set('competition_type', f.competition_type);
    if (f.date_from) p.set('date_from', f.date_from);
    if (f.date_to) p.set('date_to', f.date_to);
    return p;
}

// ── Comparador ──────────────────────────────────────────────────
let playersList = [];

async function loadPlayersList() {
    if (!TOKEN) return;
    try {
        const res = await fetch('/api/v1/stats/ranking?page_size=200', {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) return;
        const json = await res.json();
        if (!json.success || !json.data) return;
        playersList = json.data.players || [];
        populateCompareSelectors();
    } catch {
        // silent
    }
}

function populateCompareSelectors() {
    const s1 = document.getElementById('compare-p1');
    const s2 = document.getElementById('compare-p2');
    if (!s1 || !s2) return;

    const opts = playersList.map(p =>
        `<option value="${p.id}">${escHtml(p.name)} (${escHtml(p.category)})</option>`
    ).join('');

    s1.innerHTML = `<option value="">Seleccionar jugador...</option>${opts}`;
    s2.innerHTML = `<option value="">Seleccionar jugador...</option>${opts}`;
}

async function loadComparison(id1, id2) {
    const panel = document.getElementById('compare-panel');
    if (!panel) return;

    panel.innerHTML = '<div class="text-center text-gray-500 py-8 animate-pulse">Cargando comparación...</div>';
    panel.classList.remove('hidden');

    const params = buildFilterParams();
    const url = `/api/v1/stats/compare/${id1}/${id2}?${params.toString()}`;

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) {
            panel.innerHTML = '<div class="text-center text-red-400 py-8">Error al cargar la comparación</div>';
            return;
        }
        const json = await res.json();
        if (!json.success) {
            panel.innerHTML = `<div class="text-center text-red-400 py-8">${escHtml(json.error || 'Error desconocido')}</div>`;
            return;
        }
        renderComparison(json.data);
    } catch {
        panel.innerHTML = '<div class="text-center text-red-400 py-8">Error de conexión</div>';
    }
}

function renderComparison(data) {
    const panel = document.getElementById('compare-panel');
    if (!panel) return;

    const a = data.player_a;
    const b = data.player_b;

    // Player info rows for side-by-side display
    const statRows = [
        { label: 'Victorias',        keyA: a.wins,       keyB: b.wins },
        { label: 'Derrotas',         keyA: a.losses,     keyB: b.losses },
        { label: '% Victorias',       keyA: a.win_pct,    keyB: b.win_pct, suffix: '%' },
        { label: 'Partidos',         keyA: a.matches,    keyB: b.matches },
        { label: 'Sets Ganados',     keyA: a.sets_won,   keyB: b.sets_won },
        { label: 'Juegos Ganados',   keyA: a.games_won,  keyB: b.games_won },
        { label: 'Puntos FEP',       keyA: a.points,     keyB: b.points },
        { label: 'Racha Actual',     keyA: a.streak,     keyB: b.streak },
    ];

    function barPct(valA, valB) {
        const max = Math.max(Math.abs(valA), Math.abs(valB));
        if (max === 0) return 0;
        return Math.round((Math.abs(valA) / max) * 100);
    }

    function formatStreak(s) {
        if (s === 0) return '—';
        return s > 0 ? `W${s}` : `L${Math.abs(s)}`;
    }

    function avatarHtml(player) {
        if (player.avatar) {
            return `<img src="${escHtml(player.avatar)}" alt="" class="w-16 h-16 rounded-full object-cover border-2 border-[#2A2A3A]">`;
        }
        const initials = (player.name || '??').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
        return `<div class="w-16 h-16 rounded-full bg-[#2A2A3A] flex items-center justify-center text-lg font-bold text-emerald-400 border-2 border-[#3A3A4A]">${initials}</div>`;
    }

    const section = document.getElementById('compare-section');
    if (section) section.classList.remove('hidden');

    panel.innerHTML = `
        <!-- Same category notice -->
        ${!data.same_category ? `
            <div class="mb-4 p-3 rounded-lg bg-yellow-900/20 border border-yellow-700/40 text-yellow-300 text-sm">
                ⚠️ ${escHtml(data.notice || 'Distinta categoría — los puntos no son directamente comparables')}
            </div>
        ` : data.notice ? `
            <div class="mb-4 p-3 rounded-lg bg-yellow-900/20 border border-yellow-700/40 text-yellow-300 text-sm">
                ⚠️ ${escHtml(data.notice)}
            </div>
        ` : ''}

        <div class="rounded-xl border border-[#2A2A3A] overflow-hidden" style="background:#12121A;">
            <!-- Header: Player names + VS -->
            <div class="grid grid-cols-3 border-b border-[#2A2A3A]">
                <div class="p-4 text-center">
                    ${avatarHtml(a)}
                    <div class="mt-2 font-bold text-white text-lg">${escHtml(a.name)}</div>
                    <div class="text-xs text-gray-400">${escHtml(a.category)}</div>
                    ${a.position !== null ? `<div class="text-xs text-emerald-400 mt-1">#${a.position} en ranking</div>` : ''}
                    <div class="text-lg font-black mt-1" style="color:#FFD700;">🏆 ${a.points} pts</div>
                </div>
                <div class="p-4 flex items-center justify-center">
                    <div class="text-3xl font-black text-gray-500">VS</div>
                </div>
                <div class="p-4 text-center">
                    ${avatarHtml(b)}
                    <div class="mt-2 font-bold text-white text-lg">${escHtml(b.name)}</div>
                    <div class="text-xs text-gray-400">${escHtml(b.category)}</div>
                    ${b.position !== null ? `<div class="text-xs text-emerald-400 mt-1">#${b.position} en ranking</div>` : ''}
                    <div class="text-lg font-black mt-1" style="color:#FFD700;">🏆 ${b.points} pts</div>
                </div>
            </div>

            <!-- Point difference (same category) -->
            ${data.same_category && data.point_difference !== null ? `
                <div class="px-4 py-2 text-center text-sm text-gray-400 border-b border-[#2A2A3A]">
                    Diferencia de puntos: <span class="text-white font-bold">${data.point_difference} pts</span>
                </div>
            ` : ''}

            <!-- Stats comparison rows -->
            <div class="p-4 space-y-4">
                ${statRows.map(row => {
                    const valA = row.keyA;
                    const valB = row.keyB;
                    const max = Math.max(Math.abs(valA), Math.abs(valB));
                    const pctA = barPct(valA, valB);
                    const pctB = barPct(valB, valA);
                    const suffix = row.suffix || '';

                    function displayVal(v) {
                        if (row.label === 'Racha Actual') return formatStreak(v);
                        return v + suffix;
                    }

                    const barColorA = valA >= valB ? 'bg-emerald-500' : 'bg-blue-500';
                    const barColorB = valB >= valA ? 'bg-emerald-500' : 'bg-blue-500';

                    return `
                        <div>
                            <div class="flex justify-between text-xs text-gray-400 mb-1">
                                <span>${escHtml(row.label)}</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="text-sm text-white font-mono w-12 text-right shrink-0">${displayVal(valA)}</span>
                                <div class="flex-1">
                                    <div class="h-2 rounded-full bg-[#2A2A3A] overflow-hidden">
                                        <div class="h-full rounded-full ${barColorA} transition-all" style="width:${pctA}%"></div>
                                    </div>
                                </div>
                                <div class="flex-1">
                                    <div class="h-2 rounded-full bg-[#2A2A3A] overflow-hidden">
                                        <div class="h-full rounded-full ${barColorB} transition-all" style="width:${pctB}%"></div>
                                    </div>
                                </div>
                                <span class="text-sm text-white font-mono w-12 shrink-0">${displayVal(valB)}</span>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

// ── H2H ──────────────────────────────────────────────────────────
async function loadH2H(id1, id2) {
    const container = document.getElementById('h2h-content');
    if (!container) return;

    container.innerHTML = '<div class="text-center text-gray-500 py-8 animate-pulse">Cargando historial...</div>';

    const params = buildFilterParams();
    const url = `/api/v1/stats/h2h/${id1}/${id2}?${params.toString()}`;

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) {
            container.innerHTML = '<div class="text-center text-red-400 py-8">Error al cargar el historial</div>';
            return;
        }
        const json = await res.json();
        if (!json.success) {
            container.innerHTML = `<div class="text-center text-red-400 py-8">${escHtml(json.error || 'Error desconocido')}</div>`;
            return;
        }
        renderH2H(json.data);
    } catch {
        container.innerHTML = '<div class="text-center text-red-400 py-8">Error de conexión</div>';
    }
}

function renderH2H(data) {
    const container = document.getElementById('h2h-content');
    if (!container) return;

    const section = document.getElementById('h2h-section');
    if (section) section.classList.remove('hidden');

    // Get player names from the selectors
    const s1 = document.getElementById('compare-p1');
    const s2 = document.getElementById('compare-p2');
    const nameA = s1?.selectedOptions?.[0]?.text?.split(' (')[0] || 'Jugador A';
    const nameB = s2?.selectedOptions?.[0]?.text?.split(' (')[0] || 'Jugador B';
    const escA = escHtml(nameA);
    const escB = escHtml(nameB);

    if (data.total_matches === 0) {
        container.innerHTML = `
            <div class="rounded-xl border border-[#2A2A3A] p-8 text-center" style="background:#12121A;">
                <div class="text-4xl mb-3">🤷</div>
                <h3 class="text-lg font-bold text-white mb-2">Historial entre ${escA} y ${escB}</h3>
                <p class="text-gray-400">Estos jugadores todavía no se han enfrentado</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <h3 class="text-xl font-bold text-white mb-4">Historial entre Jugadores</h3>

        <!-- Summary cards -->
        <div class="grid grid-cols-3 gap-3 mb-6">
            <div class="rounded-xl border border-[#2A2A3A] p-4 text-center" style="background:#12121A;">
                <div class="text-2xl font-black text-white">${data.total_matches}</div>
                <div class="text-xs text-gray-400 mt-1">Enfrentamientos</div>
            </div>
            <div class="rounded-xl border border-[#2A2A3A] p-4 text-center" style="background:#12121A;">
                <div class="text-2xl font-black text-emerald-400">${data.wins_a}</div>
                <div class="text-xs text-gray-400 mt-1">Victorias ${escA}</div>
            </div>
            <div class="rounded-xl border border-[#2A2A3A] p-4 text-center" style="background:#12121A;">
                <div class="text-2xl font-black text-emerald-400">${data.wins_b}</div>
                <div class="text-xs text-gray-400 mt-1">Victorias ${escB}</div>
            </div>
        </div>

        <!-- Sets/Games summary -->
        <div class="grid grid-cols-2 gap-3 mb-6">
            <div class="rounded-xl border border-[#2A2A3A] p-3" style="background:#12121A;">
                <div class="text-xs text-gray-400 uppercase tracking-wider">Sets</div>
                <div class="text-white font-mono text-sm mt-1">${escA}: ${data.sets_a} · ${escB}: ${data.sets_b}</div>
            </div>
            <div class="rounded-xl border border-[#2A2A3A] p-3" style="background:#12121A;">
                <div class="text-xs text-gray-400 uppercase tracking-wider">Juegos</div>
                <div class="text-white font-mono text-sm mt-1">${escA}: ${data.games_a} · ${escB}: ${data.games_b}</div>
            </div>
        </div>

        <!-- Last match -->
        ${data.last_match ? `
            <div class="mb-4 p-3 rounded-lg bg-emerald-900/10 border border-emerald-700/30 text-sm">
                <span class="text-gray-400">Último enfrentamiento:</span>
                <span class="text-white font-medium">${escHtml(data.last_match.date || '')}</span>
                <span class="text-gray-400 mx-2">·</span>
                <span class="text-emerald-400 font-bold">${escHtml(data.last_match.winner_name || '')}</span>
                <span class="text-gray-400"> ganó </span>
                <span class="text-white font-mono">${escHtml(data.last_match.resultado || '')}</span>
            </div>
        ` : ''}

        <!-- Match history -->
        <h4 class="text-sm font-bold uppercase tracking-wider text-gray-400 mb-3">Historial de Enfrentamientos</h4>
        <div class="space-y-2">
            ${data.history.map(m => {
                const isWinA = m.winner_id === data.player_a_id;
                const isWinB = m.winner_id === data.player_b_id;
                const resultClass = isWinA ? 'text-emerald-400' : (isWinB ? 'text-red-400' : 'text-gray-400');
                return `
                    <div class="flex items-center justify-between rounded-lg border border-[#2A2A3A] p-3 text-sm" style="background:#12121A;">
                        <div class="flex items-center gap-3">
                            <span class="text-gray-500 text-xs font-mono">${escHtml(m.date || '')}</span>
                            <span class="text-white font-mono">${escHtml(m.resultado || '')}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-gray-400">Ganó</span>
                            <span class="font-semibold ${resultClass}">${escHtml(m.winner_name || '—')}</span>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// ── Compare Selector Handlers ───────────────────────────────────
function initCompareHandlers() {
    const btn = document.getElementById('compare-btn');
    const clearBtn = document.getElementById('compare-clear');
    const s1 = document.getElementById('compare-p1');
    const s2 = document.getElementById('compare-p2');

    if (!btn || !s1 || !s2) return;

    btn.addEventListener('click', () => {
        const id1 = s1.value;
        const id2 = s2.value;

        if (!id1 || !id2) {
            // Show tooltip-like feedback
            btn.textContent = 'Selecciona ambos jugadores';
            btn.style.opacity = '0.7';
            setTimeout(() => {
                btn.textContent = 'Comparar';
                btn.style.opacity = '1';
            }, 2000);
            return;
        }

        if (id1 === id2) {
            btn.textContent = 'Jugadores distintos';
            btn.style.opacity = '0.7';
            setTimeout(() => {
                btn.textContent = 'Comparar';
                btn.style.opacity = '1';
            }, 2000);
            return;
        }

        // Update URL
        const p = new URLSearchParams(window.location.search);
        p.set('compare', `${id1},${id2}`);
        history.replaceState(null, '', window.location.pathname + '?' + p.toString());

        loadComparison(id1, id2);
        loadH2H(id1, id2);
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            s1.value = '';
            s2.value = '';
            document.getElementById('compare-panel')?.classList.add('hidden');
            document.getElementById('h2h-section')?.classList.add('hidden');

            // Remove compare from URL
            const p = new URLSearchParams(window.location.search);
            p.delete('compare');
            const qs = p.toString();
            history.replaceState(null, '', qs ? window.location.pathname + '?' + qs : window.location.pathname);
        });
    }
}

// ── Handle ?compare=id1,id2 URL param ─────────────────────────
function handleCompareUrlParam() {
    const p = new URLSearchParams(window.location.search);
    const compare = p.get('compare');
    if (!compare) return;

    const parts = compare.split(',');
    if (parts.length !== 2) return;

    const [id1, id2] = parts;
    if (!id1 || !id2) return;

    // Wait for player list to populate, then select and compare
    const waitForPlayers = setInterval(() => {
        const s1 = document.getElementById('compare-p1');
        const s2 = document.getElementById('compare-p2');
        if (!s1 || !s2) return;
        if (s1.options.length > 1 && s2.options.length > 1) {
            clearInterval(waitForPlayers);

            // Check if these IDs exist in the options
            const opt1 = s1.querySelector(`option[value="${id1}"]`);
            const opt2 = s2.querySelector(`option[value="${id2}"]`);
            if (!opt1 || !opt2) {
                // If not in current page, try to load anyway
                s1.value = id1;
                s2.value = id2;
            } else {
                s1.value = id1;
                s2.value = id2;
            }

            // Scroll to compare section
            const section = document.getElementById('compare-section');
            if (section) {
                section.classList.remove('hidden');
                section.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

            loadComparison(id1, id2);
            loadH2H(id1, id2);
        }
    }, 200);
}

// ── PR #4: Community Records ────────────────────────────────────
const RECORDS_META = {
    points:           { icon: '🏆', color: '#FFD700', label: 'Puntos FEP' },
    wins:            { icon: '✅', color: '#10b981', label: 'Victorias' },
    streak:          { icon: '🔥', color: '#f97316', label: 'Racha' },
    tournaments_won: { icon: '🏅', color: '#FF6B00', label: 'Torneos Ganados' },
    finals:          { icon: '🏁', color: '#ef4444', label: 'Finales' },
    semis:           { icon: '🔶', color: '#f59e0b', label: 'Semifinales' },
    sets_won:        { icon: '📊', color: '#6366f1', label: 'Sets Ganados' },
    games_won:       { icon: '🎾', color: '#ec4899', label: 'Juegos Ganados' },
};

async function loadRecords() {
    const grid = document.getElementById('records-grid');
    const section = document.getElementById('records-section');
    if (!grid || !section) return;

    if (!TOKEN) return;

    const params = buildFilterParams();
    const url = `/api/v1/stats/records?${params.toString()}`;

    // Show skeleton
    section.classList.remove('hidden');

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) {
            section.classList.add('hidden');
            return;
        }
        const json = await res.json();
        if (!json.success || !json.data) {
            section.classList.add('hidden');
            return;
        }
        renderRecords(json.data);
    } catch {
        section.classList.add('hidden');
    }
}

function renderRecords(data) {
    const grid = document.getElementById('records-grid');
    if (!grid) return;

    if (!data || data.length === 0) {
        grid.innerHTML = '<div class="col-span-full text-center py-8"><div class="text-3xl mb-2">📭</div><p class="text-gray-400">No hay datos disponibles</p></div>';
        return;
    }

    grid.innerHTML = data.map(rec => {
        const meta = RECORDS_META[rec.metric_key] || { icon: '📊', color: '#888', label: rec.metric_label };
        const valueDisplay = rec.metric_key === 'streak'
            ? (rec.value > 0 ? `W${rec.value}` : rec.value < 0 ? `L${Math.abs(rec.value)}` : '—')
            : rec.value;
        return `
            <div class="rounded-xl border border-[#2A2A3A] p-3 card-hover opacity-0 fade-in" style="background:#12121A;">
                <div class="flex items-center gap-1.5 mb-2">
                    <span aria-hidden="true">${meta.icon}</span>
                    <span class="text-xs font-bold uppercase tracking-widest" style="color:${meta.color};">${escHtml(meta.label)}</span>
                </div>
                <div class="text-lg font-black text-white">${escHtml(String(valueDisplay))}</div>
                <a href="/player/${rec.player_id}" class="text-sm text-gray-400 hover:text-emerald-400 transition-colors truncate block">${escHtml(rec.name)}</a>
                <div class="text-xs text-gray-500">${escHtml(rec.category)}</div>
            </div>
        `;
    }).join('');

    // Trigger fade-in
    requestAnimationFrame(() => {
        grid.querySelectorAll('.fade-in').forEach(el => {
            el.style.transition = 'opacity 0.4s ease-in';
            el.style.opacity = '1';
        });
    });
}

// ── PR #4: Category Stats ────────────────────────────────────────
async function loadCategoryStats() {
    const content = document.getElementById('categories-content');
    const section = document.getElementById('categories-section');
    if (!content || !section) return;

    if (!TOKEN) return;

    const params = buildFilterParams();
    params.set('player_limit', '3');
    const url = `/api/v1/stats/categories?${params.toString()}`;

    section.classList.remove('hidden');

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) {
            section.classList.add('hidden');
            return;
        }
        const json = await res.json();
        if (!json.success || !json.data || json.data.length === 0) {
            section.classList.add('hidden');
            return;
        }
        renderCategoryStats(json.data);
    } catch {
        section.classList.add('hidden');
    }
}

function renderCategoryStats(data) {
    const content = document.getElementById('categories-content');
    if (!content) return;

    if (!data || data.length === 0) {
        content.innerHTML = '<div class="text-center py-8"><div class="text-3xl mb-2">📭</div><p class="text-gray-400">No hay datos disponibles</p></div>';
        return;
    }

    content.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        ${data.map(cat => `
            <div class="rounded-xl border border-[#2A2A3A] p-4 card-hover opacity-0 fade-in" style="background:#12121A;">
                <h3 class="text-lg font-bold text-white mb-3">${escHtml(cat.category)}</h3>
                <div class="grid grid-cols-2 gap-2 text-sm mb-3">
                    <div><span class="text-gray-400">Jugadores:</span> <span class="text-white font-semibold">${cat.total_players}</span></div>
                    <div><span class="text-gray-400">Partidos:</span> <span class="text-white font-semibold">${cat.total_matches}</span></div>
                    <div><span class="text-gray-400">Victorias:</span> <span class="text-emerald-400 font-semibold">${cat.total_wins}</span></div>
                    <div><span class="text-gray-400">Derrotas:</span> <span class="text-red-400 font-semibold">${cat.total_losses}</span></div>
                    <div><span class="text-gray-400">% Victoria:</span> <span class="text-white font-semibold">${cat.avg_win_pct}%</span></div>
                    <div><span class="text-gray-400">Prom. Puntos:</span> <span class="text-white font-semibold">${cat.avg_points}</span></div>
                </div>
                ${cat.leader_name ? `
                    <div class="text-xs text-gray-400 mb-2">
                        Líder: <span class="text-emerald-400 font-bold">${escHtml(cat.leader_name)}</span>
                        <span class="text-gray-500"> · ${cat.leader_points} pts</span>
                    </div>
                ` : ''}
                ${cat.top_players && cat.top_players.length > 0 ? `
                    <div class="border-t border-[#2A2A3A] pt-2 mt-2">
                        <div class="text-xs text-gray-400 uppercase tracking-wider mb-1.5">Top Jugadores</div>
                        ${cat.top_players.map((tp, i) => `
                            <div class="flex items-center justify-between text-xs py-0.5">
                                <span class="text-gray-500 font-mono w-4">${i + 1}.</span>
                                <a href="/player/${tp.player_id}" class="text-white hover:text-emerald-400 transition-colors flex-1 truncate">${escHtml(tp.name)}</a>
                                <span class="text-white font-semibold font-mono">${tp.value} pts</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('')}
    </div>`;

    // Trigger fade-in
    requestAnimationFrame(() => {
        content.querySelectorAll('.fade-in').forEach(el => {
            el.style.transition = 'opacity 0.4s ease-in';
            el.style.opacity = '1';
        });
    });
}

// ── PR #4: Evolution ─────────────────────────────────────────────
async function loadEvolution() {
    const content = document.getElementById('evolution-content');
    const section = document.getElementById('evolution-section');
    if (!content || !section) return;

    if (!TOKEN) return;

    const params = buildFilterParams();
    const url = `/api/v1/stats/evolution?${params.toString()}`;

    section.classList.remove('hidden');

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) {
            section.classList.add('hidden');
            return;
        }
        const json = await res.json();
        if (!json.success || !json.data) {
            section.classList.add('hidden');
            return;
        }
        renderEvolution(json.data);
    } catch {
        section.classList.add('hidden');
    }
}

function renderEvolution(data) {
    const content = document.getElementById('evolution-content');
    if (!content) return;

    if (!data || data.length === 0) {
        content.innerHTML = '<div class="text-center py-8"><div class="text-3xl mb-2">📭</div><p class="text-gray-400">No hay datos disponibles</p></div>';
        return;
    }

    content.innerHTML = `
        <div class="rounded-xl border border-[#2A2A3A] overflow-x-auto" style="background:#12121A;">
            <table class="w-full text-sm">
                <thead>
                    <tr class="border-b border-[#2A2A3A] text-gray-400 text-xs uppercase tracking-wider">
                        <th class="p-3 text-left">Nombre</th>
                        <th class="p-3 text-left">Categoría</th>
                        <th class="p-3 text-right">Puntos</th>
                        <th class="p-3 text-right">Evolución</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(e => `
                        <tr class="border-b border-[#2A2A3A] hover:bg-white/5 transition-colors">
                            <td class="p-3">
                                <a href="/player/${e.player_id}" class="text-white font-medium hover:text-emerald-400 transition-colors">${escHtml(e.name)}</a>
                            </td>
                            <td class="p-3 text-gray-400 text-xs">${escHtml(e.category)}</td>
                            <td class="p-3 text-right text-white font-semibold font-mono">${e.current_points}</td>
                            <td class="p-3 text-right text-gray-500 text-xs">${e.sparkline && e.sparkline.length > 0 ? '📈' : '— Prep. históricos'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ── PR #4: Community Highlights ─────────────────────────────────
async function loadCommunityHighlights() {
    const container = document.getElementById('community-content');
    const card = document.getElementById('community-highlights');
    if (!container || !card) return;

    if (!TOKEN) return;

    const params = buildFilterParams();
    const url = `/api/v1/stats/community?${params.toString()}`;

    card.classList.remove('hidden');

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        if (!res.ok) {
            card.classList.add('hidden');
            return;
        }
        const json = await res.json();
        if (!json.success || !json.data) {
            card.classList.add('hidden');
            return;
        }
        renderCommunityHighlights(json.data);
    } catch {
        card.classList.add('hidden');
    }
}

function renderCommunityHighlights(data) {
    const container = document.getElementById('community-content');
    if (!container) return;

    if (!data) {
        container.innerHTML = '<div class="text-center py-4 text-gray-500">Sin datos de comunidad</div>';
        return;
    }

    function playerRow(icon, label, player, extra) {
        if (!player) return '';
        return `
            <div class="flex items-center justify-between py-2 border-b border-[#2A2A3A]/50 last:border-0">
                <div class="flex items-center gap-2 min-w-0">
                    <span aria-hidden="true">${icon}</span>
                    <span class="text-xs text-gray-400 shrink-0">${escHtml(label)}</span>
                </div>
                <div class="text-right min-w-0 ml-2">
                    <a href="/player/${player.id}" class="text-sm text-white font-medium hover:text-emerald-400 transition-colors truncate block">${escHtml(player.name)}</a>
                    <div class="text-xs text-gray-500">
                        ${player.points ? player.points + ' pts · ' : ''}${player.win_pct}% · ${escHtml(player.category)}
                        ${extra ? ' · ' + extra : ''}
                    </div>
                </div>
            </div>
        `;
    }

    let rows = '';

    rows += playerRow('🏆', 'Más Puntos', data.most_points);
    rows += playerRow('⭐', 'Mejor Forma', data.best_form);

    if (data.best_pair) {
        rows += `
            <div class="flex items-center justify-between py-2 border-b border-[#2A2A3A]/50 last:border-0">
                <div class="flex items-center gap-2 min-w-0">
                    <span aria-hidden="true">🤝</span>
                    <span class="text-xs text-gray-400 shrink-0">Mejor Pareja</span>
                </div>
                <div class="text-right min-w-0 ml-2">
                    <div class="text-sm text-white font-medium">${escHtml(data.best_pair.player1_name)} + ${escHtml(data.best_pair.player2_name)}</div>
                    <div class="text-xs text-gray-500">${data.best_pair.win_pct}% · ${data.best_pair.matches} partidos</div>
                </div>
            </div>
        `;
    }

    rows += playerRow('⚡', 'Más Activo', data.most_active);

    if (!rows) {
        rows = '<div class="text-center py-4 text-gray-500">Sin datos de comunidad</div>';
    }

    container.innerHTML = rows;
}

// ── PR #4: Polish — CSS Animations ──────────────────────────────
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .fade-in { opacity: 0; }
        .section-transition {
            transition: opacity 0.3s ease-in-out;
        }
        .sort-highlight {
            transition: color 0.2s ease;
        }
        html {
            scroll-behavior: smooth;
        }
        @media (max-width: 640px) {
            .overflow-x-auto {
                -webkit-overflow-scrolling: touch;
            }
        }
    `;
    document.head.appendChild(style);
}

// ── Init ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    addAnimationStyles();
    loadSummary();
    initRankingLazyLoad();

    // PR #3: Load top players (visible by default, hidden until data)
    loadTopPlayers();

    // PR #4: Load new sections with slight delay for progressive loading
    setTimeout(() => {
        loadRecords();
        loadCategoryStats();
        loadEvolution();
    }, 100);

    // PR #3: Init compare handlers after a short delay to let ranking load
    setTimeout(() => {
        loadPlayersList();
        initCompareHandlers();
        handleCompareUrlParam();
        loadCommunityHighlights();
    }, 300);
});
