// player_utils.js — Pure utility functions
// PR #2: Extract from player_detail.html inline script
// No DOM, no state, no API calls

// ── String utilities ──────────────────────────────────────────────

function escapeHtml(str) {
    return (str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

function removeAccentAndLowerCase(text) {
    if (!text) return '';
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
}

// ── Formatting utilities ──────────────────────────────────────────

function nivelAmenazaFromScore(score) {
    if (score >= 90) return 'MUY ALTO';
    if (score >= 70) return 'ALTO';
    if (score >= 50) return 'MEDIO';
    return 'BAJO';
}

function dragonBallCount(nivel) {
    return { 'BAJO': 1, 'MEDIO': 3, 'ALTO': 5, 'MUY ALTO': 7 }[nivel] || 1;
}

function getMatchTypeBadge(match) {
    const isTorneo = match.tournament_id || (match.torneo && match.torneo.trim() !== '');
    return isTorneo
        ? { text: 'Torneo', color: '#FFD700', bgColor: 'rgba(255,215,0,0.1)' }
        : { text: 'Amistoso', color: '#FF6B00', bgColor: 'rgba(255,107,0,0.1)' };
}

function hasLesionNote(notes) {
    return (notes || '').toLowerCase().match(/lesi[oó]n|retiro|retirada|abandono/i);
}

function resolveCategoryKey(categoryValue) {
    const mapping = {
        'INICIACION': 'Iniciación',
        'QUINTA': '5ª Categoría',
        'CUARTA': '4ª Categoría',
        'TERCERA': '3ª Categoría',
        'SEGUNDA': '2ª Categoría',
        'PRIMERA': '1ª Categoría',
        'PRO': 'Profesional',
        'Iniciación': 'Iniciación',
        '5ª Categoría': '5ª Categoría',
        '4ª Categoría': '4ª Categoría',
        '3ª Categoría': '3ª Categoría',
        '2ª Categoría': '2ª Categoría',
        '1ª Categoría': '1ª Categoría',
        'Profesional': 'Profesional',
    };
    return mapping[categoryValue] ?? categoryValue;
}

function getTournamentNameById(id) {
    if (!id) return '';
    const t = loadedTournaments.find(t => t.id === id);
    return t ? t.name : '';
}

// ── Notification utilities ────────────────────────────────────────

function showToast(msg, type) {
    const existing = document.querySelector('.toast-msg');
    if (existing) existing.remove();
    const div = document.createElement('div');
    div.className = 'toast-msg fixed top-4 right-4 px-5 py-3 rounded-xl text-sm font-bold z-[9999] shadow-2xl';
    div.style.background = type === 'error' ? '#dc2626' : '#16a34a';
    div.style.color = '#fff';
    div.textContent = msg;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 3000);
}
