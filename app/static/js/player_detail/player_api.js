/**
 * player_api.js
 *
 * ÚNICA responsabilidad: fetch + devolver datos.
 * NUNCA toca DOM, state, ni modales.
 *
 * Reglas (tolerancia cero):
 * - ✅ devuelve datos (Promise con objeto/array) o lanza excepción
 * - ❌ NUNCA hace document.getElementById ni window.DOM
 * - ❌ NUNCA hace showToast
 * - ❌ NUNCA abre modales
 * - ❌ NUNCA modifica state
 *
 * Script clásico (no module) — compatible con inline script legacy.
 * En PR #8 pasará a módulo ES importado por player_detail.js.
 */

// ── Internal helpers ──────────────────────────────────────────

function __apiHeaders(contentType) {
    const token = localStorage.getItem('access_token');
    const headers = { 'Authorization': `Bearer ${token}` };
    if (contentType !== false) headers['Content-Type'] = 'application/json';
    return headers;
}

async function __throwWithStatus(res) {
    let data;
    try { data = await res.json(); } catch (e) { data = {}; }
    const err = new Error(data.detail || `HTTP ${res.status}`);
    err.status = res.status;
    err.detail = data.detail || data;
    throw err;
}

// ── Player ─────────────────────────────────────────────────────

async function fetchPlayer(playerId) {
    const res = await fetch(`/api/v1/players/${playerId}`, {
        headers: __apiHeaders()
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

async function fetchAnalyses(playerId) {
    const res = await fetch(`/api/v1/analysis/${playerId}`, {
        headers: __apiHeaders()
    });
    if (res.ok) return await res.json();
    return [];
}

// ── Matches ────────────────────────────────────────────────────

async function fetchMatches(playerId, filter) {
    let url = `/api/v1/players/${playerId}/matches`;
    if (filter === 'amistoso') {
        url += '?tournament_id=none';
    } else if (filter && filter !== 'all') {
        url += `?tournament_id=${filter}`;
    }
    const res = await fetch(url, { headers: __apiHeaders() });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

async function saveMatch(playerId, payload) {
    const res = await fetch(`/api/v1/players/${playerId}/matches`, {
        method: 'POST',
        headers: __apiHeaders(),
        body: JSON.stringify(payload)
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

async function updateMatch(matchId, playerId, payload) {
    const res = await fetch(`/api/v1/players/${playerId}/matches/${matchId}`, {
        method: 'PUT',
        headers: __apiHeaders(),
        body: JSON.stringify(payload)
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

async function deleteMatch(matchId, playerId) {
    const res = await fetch(`/api/v1/players/${playerId}/matches/${matchId}`, {
        method: 'DELETE',
        headers: __apiHeaders()
    });
    if (!res.ok) await __throwWithStatus(res);
    return { success: true };
}

// ── Tournaments ────────────────────────────────────────────────

async function fetchTournaments(playerId) {
    const res = await fetch(`/api/v1/tournaments/?player_id=${playerId}`, {
        headers: __apiHeaders()
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

async function createTournament(payload) {
    const res = await fetch('/api/v1/tournaments/', {
        method: 'POST',
        headers: __apiHeaders(),
        body: JSON.stringify(payload)
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

async function updateTournament(tournamentId, payload) {
    const res = await fetch(`/api/v1/tournaments/${tournamentId}`, {
        method: 'PUT',
        headers: __apiHeaders(),
        body: JSON.stringify(payload)
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

async function deleteTournamentApi(tournamentId) {
    const res = await fetch(`/api/v1/tournaments/${tournamentId}`, {
        method: 'DELETE',
        headers: __apiHeaders()
    });
    if (res.status !== 204) await __throwWithStatus(res);
    return { success: true };
}

// ── Players list (for partner dropdown) ────────────────────────

async function fetchAllPlayers() {
    const res = await fetch('/api/v1/players/', {
        headers: __apiHeaders()
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

// ── Stats (computed) ──────────────────────────────────────────

async function fetchPlayerStats(playerId) {
    const res = await fetch(`/api/v1/players/${playerId}/stats`, {
        headers: __apiHeaders()
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

// ── Player update (save + re-analyze) ─────────────────────────

async function updatePlayer(playerId, payload) {
    const res = await fetch(`/api/v1/players/${playerId}`, {
        method: 'PUT',
        headers: __apiHeaders(),
        body: JSON.stringify(payload)
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

// ── Analytics ──────────────────────────────────────────────────

async function fetchMatchAnalytics(playerId) {
    const res = await fetch(`/api/v1/players/${playerId}/analytics`, {
        headers: __apiHeaders()
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}

async function analyzePlayer(playerId) {
    const res = await fetch(`/api/v1/analysis/${playerId}`, {
        method: 'POST',
        headers: __apiHeaders()
    });
    if (!res.ok) await __throwWithStatus(res);
    return await res.json();
}
