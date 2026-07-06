/**
 * player_detail.js
 *
 * Orchestrator — calls API, sets state, calls render.
 * PR #7 — Integration phase.
 *
 * Reglas:
 * - Único archivo que importa módulos ES
 * - No define render/CRUD
 * - No importa otro módulo
 * - API → state → render
 */

import { state } from './player_state.js';
import { DOM } from './player_dom.js';

window.state = state;
window.DOM = DOM;

export async function initPlayerDetail() {
    const playerId = window.location.pathname.split('/').pop();
    state.playerId = playerId;
    window.playerId = playerId;
    window.token = localStorage.getItem('access_token');
    if (!window.token) { window.location.href = '/login'; return; }

    // Load player + analysis
    const [player, analyses] = await Promise.all([
        fetchPlayer(playerId),
        fetchAnalyses(playerId)
    ]);
    state.player = player;
    renderPlayer(player, analyses);

    // Load matches
    const matches = await fetchMatches(playerId, window.currentFilter || 'all');
    state.matches = matches;
    window.allServerMatches = matches;
    filterMatchesBySearch();

    // Load tournaments
    const tournaments = await fetchTournaments(playerId);
    state.tournaments = tournaments;
    renderTournaments(tournaments, 'm-torneo-select');
    filterMatchHistory();
    setSortMode('date-desc');
}

async function reloadPlayer() {
    const playerId = window.playerId;
    const [player, analyses] = await Promise.all([
        fetchPlayer(playerId),
        fetchAnalyses(playerId)
    ]);
    state.player = player;
    renderPlayer(player, analyses);
    loadMatches();
}

// Bridge for classic scripts (player_analytics.js)
window.reloadPlayer = reloadPlayer;

// ── Auto-init ────────────────────────────────────────────
initPlayerDetail();
