/**
 * player_modals.js
 *
 * Modal open/close logic.
 * PR #5 — Extracted from player_detail.html inline script.
 *
 * Restricciones:
 * - No estado
 * - No fetch
 * - Solo abrir/cerrar modales y validación de inputs
 */

// ── Stats Modal ───────────────────────────────────────────────
function openStatsModal() {
    if (!state.player) return;
    const p = state.player;

    const numColors = {
        'stats-tecnica': '#FF6B00',
        'stats-fisico': '#00B4D8',
        'stats-mental': '#00FF87',
    };
    const renderBars = (containerId, stats, color) => {
        const valColor = numColors[containerId] || '#ffffff';
        document.getElementById(containerId).innerHTML = stats.map(([label, val]) => `
            <div>
                <div class="flex justify-between mb-1">
                    <span class="text-xs font-orbitron" style="color:#94a3b8;">${label}</span>
                    <span class="text-xs font-bold font-orbitron" style="color:${valColor};">${val ?? 50}</span>
                </div>
                <div class="h-1.5 rounded-full overflow-hidden" style="background:#0A0A0F;">
                    <div class="h-full rounded-full"
                        style="width:${val ?? 50}%;background:${color};transition:width 0.8s ease;"></div>
                </div>
            </div>`).join('');
    };

    renderBars('stats-tecnica', [
        ['Derecha', p.derecha], ['Revés', p.reves],
        ['Volea Derecha', p.volea_derecha], ['Volea Revés', p.volea_reves],
        ['Bandeja', p.bandeja], ['Víbora', p.vibora], ['Remate', p.remate],
        ['Globo', p.globo], ['Saque', p.saque], ['Bajada de pared', p.bajada_pared]
    ], 'linear-gradient(90deg,#FF6B00,#FFD700)');

    renderBars('stats-fisico', [
        ['Velocidad', p.velocidad], ['Resistencia', p.resistencia], ['Reflejos', p.reflejos]
    ], 'linear-gradient(90deg,#00B4D8,#06B6D4)');

    renderBars('stats-mental', [
        ['Táctica', p.tactica], ['Presión', p.presion], ['Trabajo en pareja', p.trabajo_en_pareja]
    ], 'linear-gradient(90deg,#00FF87,#22D3EE)');

    // Mostrar con animación
    const modal = document.getElementById('stats-modal');
    modal.classList.remove('hidden');
    modal.style.opacity = '0';
    setTimeout(() => { modal.style.transition = 'opacity 0.2s'; modal.style.opacity = '1'; }, 10);
}

function closeStatsModal() {
    document.getElementById('stats-modal').classList.add('hidden');
}

// ── Match Analytics Modal ─────────────────────────────────────
function closeMatchAnalyticsModal() {
    document.getElementById('match-analytics-modal').classList.add('hidden');
    document.getElementById('analytics-content').classList.add('hidden');
    document.getElementById('analytics-loading').classList.remove('hidden');
    document.getElementById('analytics-loading').innerHTML = '<p class="text-gray-500 text-sm">Cargando análisis...</p>';
}

// ── Level Guide Modal ─────────────────────────────────────────
function openLevelGuideModal() {
    document.getElementById('level-guide-modal').classList.remove('hidden');
}
function closeLevelGuideModal() {
    document.getElementById('level-guide-modal').classList.add('hidden');
}

// ── Edit Modal ────────────────────────────────────────────────
function openEditModal() {
    if (!state.player) return;
    const p = state.player;

    document.getElementById('edit-name').value = p.name;
    document.getElementById('edit-category').value = resolveCategoryKey(p.category);

    const fields = ['derecha','reves','volea_derecha','volea_reves','bandeja','vibora','remate','globo','saque',
        'bajada_pared','velocidad','resistencia','reflejos','tactica','presion',
        'trabajo_en_pareja'];
    fields.forEach(f => {
        const el = document.getElementById(`e-${f}`);
        if (el) el.value = p[f] ?? 50;
    });

    document.getElementById('edit-error').classList.add('hidden');
    document.getElementById('edit-modal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('edit-modal').classList.add('hidden');
}

function sanitizeEditPlayerNumbers() {
    document.querySelectorAll('#edit-modal input[type="number"]').forEach(el => {
        el.addEventListener('input', () => {
            el.value = el.value.replace(/[^0-9]/g, '');
        });
    });
}

// ── Full Match History ────────────────────────────────────────
function openFullMatchHistory() {
    const modal = document.getElementById('match-history-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    renderFullMatchHistory(state.matches);
}

function openSearchedMatchHistory() {
    const modal = document.getElementById('match-history-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    renderFullMatchHistory(searchedMatches || state.matches);
}

function closeMatchHistoryModal() {
    const modal = document.getElementById('match-history-modal');
    if (!modal) return;
    modal.classList.add('hidden');
}

// ── Match Modal ───────────────────────────────────────────────
function closeMatchModal() {
    resetMatchForm();
    document.getElementById('match-modal').classList.add('hidden');
    // Reset button state
    const btn = document.getElementById('btn-save-match');
    if (btn) {
        btn.dataset.matchId = '';
        btn.textContent = '💾 Guardar partido';
    }
}
