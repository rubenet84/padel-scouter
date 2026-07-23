/**
 * match_renderer.js
 *
 * Match card rendering, match list, full history, and sorting.
 * PR #6B — Extracted from player_detail.html inline script.
 *
 * Restricciones:
 * - No fetch, no API calls
 * - No CRUD (edit/delete/save)
 * - renderMatchCard() es pura construcción de HTML
 * - Accede al DOM via document.getElementById (window.DOM no necesario aquí)
 * - Script clásico (no module)
 */

// ── Render Single Match Card ─────────────────────────────────
function renderMatchCard(m) {
    const ganado = m.ganado;
    const color   = ganado ? '#00FF87' : '#FF2D2D';
    const bgColor = ganado ? 'rgba(0,255,135,0.08)' : 'rgba(255,45,45,0.08)';
    const label   = ganado ? '🏆' : '❌';
    const badgeColor = ganado ? 'rgba(0,255,135,0.1)' : 'rgba(255,45,45,0.1)';
    const badgeText  = ganado ? 'Victoria' : 'Derrota';
    const typeBadge  = getMatchTypeBadge(m);
    const lesion    = hasLesionNote(m.notes);
    const lesionBadge = lesion
        ? `<span class="px-1.5 py-0.5 text-xs font-bold rounded uppercase tracking-wider" style="background:rgba(239,68,68,0.12);color:#ef4444;">🩹 Lesión</span>`
        : '';
    const fecha = new Date(m.played_at).toLocaleDateString('es-ES', {day:'numeric', month:'short'});
    const rival   = escapeHtml(m.rival_nombre) || 'Rival';
    const resultado = escapeHtml(m.resultado || '—');
    const ronda   = m.ronda ? `· ${escapeHtml(m.ronda)}` : '';
    const tName   = getTournamentNameById(m.tournament_id, state.tournaments);
    const torneo  = tName ? `· ${escapeHtml(tName)}` : '';
    const scoring = { 'con_ventaja':'Con Ventaja','star_point':'Star Point','punto_oro':'Punto Oro' }[m.scoring_method] || '';
    const notas   = m.notes ? escapeHtml(m.notes) : '';
    const notasHtml = notas ? `<p class="text-xs mt-1 italic" style="color:#64748b;">📝 ${notas}</p>` : '';
    // Partner display — swap when viewed from partner's profile
    let partnerDisplay = '';
    if (m.partner_id) {
        if (playerId === m.partner_id) {
            // Viewer IS the partner → show "con [player1]" linking to player1
            partnerDisplay = ` · con <a href="/player/${m.player1_id}" style="color:#a855f7;text-decoration:underline;">${escapeHtml(m.player1_name || 'Jugador')}</a>`;
        } else {
            partnerDisplay = ` · con <a href="/player/${m.partner_id}" style="color:#a855f7;text-decoration:underline;">${escapeHtml(m.partner_nombre || 'Compañero')}</a>`;
        }
    } else if (m.partner_nombre) {
        partnerDisplay = ` · con ${escapeHtml(m.partner_nombre)}`;
    }

    return `
        <div class="flex items-center gap-4 p-3.5 rounded-xl transition-all"
            style="background:rgba(10,10,15,0.5);border:1px solid rgba(42,42,58,0.3);">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                style="background:${bgColor};">
                <span class="text-base" style="color:${color};">${label}</span>
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                    <p class="text-sm font-semibold text-white">vs. ${rival}${partnerDisplay}</p>
                    <span class="px-1.5 py-0.5 text-xs font-bold rounded uppercase tracking-wider"
                        style="background:${typeBadge.bgColor};color:${typeBadge.color};">${typeBadge.text}</span>
                    <span class="px-1.5 py-0.5 text-xs font-bold rounded uppercase tracking-wider"
                        style="background:${badgeColor};color:${color};">${badgeText}</span>
                    ${lesionBadge}
                </div>
                <p class="text-xs mt-0.5" style="color:#475569;">${ronda} ${scoring} ${torneo} · ${fecha}</p>
                ${notasHtml}
            </div>
            <div class="text-right flex-shrink-0 flex items-center gap-2">
                <p class="text-sm font-bold text-white mr-2">${resultado}</p>
                <button onclick="openEditMatchModal('${m.id}')" 
                        class="px-2 py-1 rounded-lg text-xs font-bold transition-all hover:scale-105"
                        style="background:rgba(255,107,0,0.2);border:1px solid rgba(255,107,0,0.3);color:#FF6B00;"
                        title="Editar partido">✏️</button>
                ${playerId === m.player1_id ? `
                <button onclick="deleteMatch('${m.id}')" 
                        class="px-2 py-1 rounded-lg text-xs font-bold transition-all hover:scale-105"
                        style="background:rgba(239,68,68,0.2);border:1px solid rgba(239,68,68,0.3);color:#ef4444;"
                        title="Eliminar partido">🗑️</button>
                ` : ''}
            </div>
        </div>`;
}

// ── Render Matches (preview list) ────────────────────────────
function renderMatches(matches, emptyMsg, searchTotalCount) {
    state.matches = matches || [];
    const container = document.getElementById('matches-section');
    if (!container) return;
    container.classList.remove('hidden');

    const list = document.getElementById('matches-list');
    if (!matches || matches.length === 0) {
        list.innerHTML = `<div class="text-center py-8 text-sm" style="color:#475569;">${escapeHtml(emptyMsg || 'Sin partidos registrados aún')}</div>`;
        return;
    }

    const totalCount = searchTotalCount || matches.length;
    const preview = matches.slice(0, 3);
    const previewHtml = preview.map(m => renderMatchCard(m)).join('');

    let moreButton = '';
    if (totalCount > 3) {
        const isSearch = searchTotalCount > 0;
        const label = isSearch
            ? `Hay ${searchTotalCount} resultados. <span style="color:#a855f7;text-decoration:underline;">Ver en el historial</span>`
            : 'Ver todo el historial de combate';
        const onclick = isSearch ? "openSearchedMatchHistory()" : "openFullMatchHistory()";
        moreButton = `
            <div class="pt-3 text-center">
                <button onclick="${onclick}"
                        class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all font-orbitron hover:brightness-125 hover:scale-105"
                        style="background:rgba(168,85,247,0.1);border:1px solid rgba(168,85,247,0.2);color:#a855f7;">
                    ${label}
                </button>
            </div>
        `;
    }

    list.innerHTML = previewHtml + moreButton;
}

// ── Render Full Match History ────────────────────────────────
function renderFullMatchHistory(matches) {
    const container = document.getElementById('match-history-list');
    if (!container) return;
    if (!matches || matches.length === 0) {
        container.innerHTML = `<div class="text-center py-8 text-sm" style="color:#475569;">Sin partidos registrados aún</div>`;
        return;
    }
    const sorted = sortMatches(matches);
    container.innerHTML = sorted.map(m => renderMatchCard(m)).join('');
}

// ── Sort controls for full match history ──
let sortMode = 'date-desc';

function setSortMode(mode) {
    sortMode = mode;
    // Update button styles
    ['sort-date-desc', 'sort-date-asc', 'sort-round', 'sort-round-desc'].forEach(id => {
        const btn = document.getElementById(id);
        if (!btn) return;
        if (id === 'sort-' + mode) {
            btn.style.background = 'rgba(168,85,247,0.2)';
            btn.style.border = '1px solid rgba(168,85,247,0.3)';
            btn.style.color = '#a855f7';
        } else {
            btn.style.background = 'rgba(168,85,247,0.05)';
            btn.style.border = '1px solid rgba(42,42,58,0.3)';
            btn.style.color = '#5F5285';
        }
    });
    // Re-render if modal is open
    const modal = document.getElementById('match-history-modal');
    if (!modal || modal.classList.contains('hidden')) return;
    const container = document.getElementById('match-history-list');
    if (!container) return;
    const isSearchActive = searchedMatches && document.getElementById('mh-filter-search').value.trim();
    renderFullMatchHistory(isSearchActive ? searchedMatches : state.matches);
}

function sortMatches(matches) {
    const sorted = [...matches];
    if (sortMode === 'date-desc') {
        sorted.sort((a, b) => new Date(b.played_at) - new Date(a.played_at));
    } else if (sortMode === 'date-asc') {
        sorted.sort((a, b) => new Date(a.played_at) - new Date(b.played_at));
    } else if (sortMode === 'round') {
        sorted.sort((a, b) => {
            const idxA = a.ronda ? ROUND_ORDER.indexOf(a.ronda) : -1;
            const idxB = b.ronda ? ROUND_ORDER.indexOf(b.ronda) : -1;
            if (idxA === -1 && idxB === -1) return 0;
            if (idxA === -1) return 1;
            if (idxB === -1) return -1;
            return idxA - idxB;
        });
    } else if (sortMode === 'round-desc') {
        sorted.sort((a, b) => {
            const idxA = a.ronda ? ROUND_ORDER.indexOf(a.ronda) : -1;
            const idxB = b.ronda ? ROUND_ORDER.indexOf(b.ronda) : -1;
            if (idxA === -1 && idxB === -1) return 0;
            if (idxA === -1) return 1;
            if (idxB === -1) return -1;
            return idxB - idxA;
        });
    }
    return sorted;
}

// ── Round hierarchy ──────────────────────────────────────────
const ROUND_ORDER = [
    'Fase de grupos',
    '32avos',
    '16avos',
    'Octavos',
    'Cuartos',
    'Semifinal',
    'Final',
];

function getRoundIndex(roundName) {
    return ROUND_ORDER.indexOf(roundName);
}
