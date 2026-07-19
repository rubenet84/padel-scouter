/**
 * player_analytics.js
 *
 * Analytics features for player detail page.
 * PR #8B — Extracted from player_detail.html inline script.
 *
 * Dependencias:
 * - player_api.js (analyzePlayer, fetchMatchAnalytics, updatePlayer)
 * - player_detail.js (reloadPlayer)
 * - player_modals.js (closeEditModal)
 *
 * Classic script (no module) — global functions for onclick handlers.
 */

// ── Analyze Now ────────────────────────────────────────────────
// Triggered by the "Analizar con IA" button. Calls the API,
// then reloads player data via reloadPlayer().

async function analyzeNow() {
    const btn = document.getElementById('btn-analyze');
    btn.textContent = '⏳ Analizando...';
    btn.disabled = true;
    btn.style.opacity = '0.6';

    try {
        await analyzePlayer(window.playerId);
        await reloadPlayer();
    } catch (e) {
        alert('Error al analizar. Inténtalo de nuevo.');
    } finally {
        btn.textContent = '🔮 Nuevo análisis IA';
        btn.disabled = false;
        btn.style.opacity = '1';
    }
}

// ── Match Analytics Modal ──────────────────────────────────────
// Opens the modal and populates all analytics data via
// fetchMatchAnalytics (player_api.js).

async function openMatchAnalyticsModal() {
    const modal = document.getElementById('match-analytics-modal');
    modal.classList.remove('hidden');
    modal.style.opacity = '0';
    setTimeout(() => { modal.style.transition = 'opacity 0.2s'; modal.style.opacity = '1'; }, 10);

    document.getElementById('analytics-loading').classList.remove('hidden');
    document.getElementById('analytics-content').classList.add('hidden');

    try {
        const a = await fetchMatchAnalytics(window.playerId);

        // Totales
        document.getElementById('a-total-partidos').textContent = a.total_partidos;
        document.getElementById('a-victorias').textContent = a.victorias;
        document.getElementById('a-derrotas').textContent = a.derrotas;
        document.getElementById('a-win-rate').textContent = a.win_rate.toFixed(1) + '%';

        // Sets
        document.getElementById('a-total-sets').textContent = a.total_sets;
        document.getElementById('a-sets-ganados').textContent = a.sets_ganados;
        document.getElementById('a-sets-perdidos').textContent = a.sets_perdidos;
        document.getElementById('a-set-ratio').textContent = (a.set_ratio * 100).toFixed(0) + '%';
        const total = a.partidos_2_sets + a.partidos_3_sets;
        const pct2 = total > 0 ? (a.partidos_2_sets / total * 100).toFixed(0) : '0';
        const pct3 = total > 0 ? (a.partidos_3_sets / total * 100).toFixed(0) : '0';
        document.getElementById('a-2-sets').textContent = a.partidos_2_sets;
        document.getElementById('a-2-sets-ratio').textContent = pct2 + '%';
        document.getElementById('a-3-sets').textContent = a.partidos_3_sets;
        document.getElementById('a-3-sets-ratio').textContent = pct3 + '%';

        // Torneos / Amistosos
        document.getElementById('a-torneos').textContent = a.torneos_jugados;
        document.getElementById('a-amistosos').textContent = a.amistosos_jugados;

        // Mejor ronda
        const mejorRow = document.getElementById('a-mejor-ronda-row');
        if (a.mejor_ronda) {
            document.getElementById('a-mejor-ronda').textContent = a.mejor_ronda;
            mejorRow.classList.remove('hidden');
        } else {
            mejorRow.classList.add('hidden');
        }

        // Desglose de rondas
        const rondasSection = document.getElementById('a-rondas-section');
        const rondasList = document.getElementById('a-rondas-list');
        const roundKeys = Object.keys(a.rondas_breakdown);
        if (roundKeys.length > 0) {
            rondasList.innerHTML = roundKeys.map(r => {
                const count = a.rondas_breakdown[r];
                return `
                    <div class="flex items-center gap-3 px-3 py-2 rounded-lg" style="background:rgba(10,10,15,0.6);border:1px solid rgba(42,42,58,0.4);">
                        <span class="text-xs font-semibold flex-1" style="color:#cbd5e1;">${r}</span>
                        <div class="flex-1 h-2 rounded-full overflow-hidden" style="background:#0A0A0F;">
                            <div class="h-full rounded-full" style="width:${(count / Math.max(...Object.values(a.rondas_breakdown))) * 100}%;background:linear-gradient(90deg,#a855f7,#06B6D4);"></div>
                        </div>
                        <span class="text-xs font-bold" style="color:#a855f7;min-width:2rem;text-align:right;">${count}${count > 1 ? ' veces' : ' vez'}</span>
                    </div>`;
            }).join('');
            rondasSection.classList.remove('hidden');
        } else {
            rondasSection.classList.add('hidden');
        }

        // Fase media
        if (a.fase_media_nombre) {
            document.getElementById('a-fase-media').textContent = a.fase_media_nombre;
        } else {
            document.getElementById('a-fase-media').textContent = '—';
        }

        // Scoring breakdown
        const scoringList = document.getElementById('a-scoring-list');
        const scoringEntries = Object.entries(a.scoring_breakdown);
        if (scoringEntries.length > 0) {
            scoringList.innerHTML = scoringEntries.map(([label, count]) => `
                <div class="text-center p-3 rounded-lg" style="background:rgba(10,10,15,0.6);border:1px solid rgba(42,42,58,0.4);">
                    <p class="text-lg font-bold text-white font-orbitron">${count}</p>
                    <p class="text-xs uppercase tracking-wider font-orbitron" style="color:#475569;">${label}</p>
                </div>
            `).join('');
        } else {
            scoringList.innerHTML = '<p class="text-xs text-gray-500 col-span-3 text-center py-4">Sin datos</p>';
        }

        document.getElementById('analytics-loading').classList.add('hidden');
        document.getElementById('analytics-content').classList.remove('hidden');
    } catch (e) {
        console.warn('match analytics error:', e);
        document.getElementById('analytics-loading').innerHTML = '<p class="text-red-400 text-sm">Error al cargar análisis</p>';
    }
}

// ── Save and Analyze ───────────────────────────────────────────
// Validates the edit form, saves player data, re-runs AI analysis,
// closes the modal, and reloads player data.

async function saveAndAnalyze() {
    const btn = document.getElementById('btn-save');
    const errEl = document.getElementById('edit-error');
    errEl.classList.add('hidden');

    const name = document.getElementById('edit-name').value.trim();
    if (!name) {
        errEl.textContent = 'El nombre del jugador es obligatorio.';
        errEl.classList.remove('hidden');
        return;
    }

    const stats = {};
    const statFields = ['derecha','reves','volea_derecha','volea_reves','bandeja','vibora','remate','globo','saque',
        'bajada_pared','velocidad','resistencia','reflejos','tactica','presion',
        'trabajo_en_pareja'];

    for (const f of statFields) {
        const raw = document.getElementById(`e-${f}`)?.value ?? '';
        const value = Number(raw);

        if (!Number.isFinite(value) || raw.trim() === '' || !Number.isInteger(value)) {
            errEl.textContent = `El valor de ${f.replace('_', ' ')} debe ser un número entero válido.`;
            errEl.classList.remove('hidden');
            return;
        }

        if (value < 0 || value > 100) {
            errEl.textContent = `El valor de ${f.replace('_', ' ')} debe estar entre 0 y 100.`;
            errEl.classList.remove('hidden');
            return;
        }

        stats[f] = value;
    }

    btn.textContent = '⏳ Guardando...';
    btn.disabled = true;
    btn.style.opacity = '0.6';

    try {
        const body = {
            name,
            category: document.getElementById('edit-category').value,
            mano: document.getElementById('edit-mano')?.value || 'Derecha',
            stats
        };

        await updatePlayer(window.playerId, body);

        // Relanzar análisis IA
        btn.textContent = '🔮 Analizando con IA...';
        await analyzePlayer(window.playerId);

        closeEditModal();
        await reloadPlayer();

    } catch(e) {
        errEl.textContent = e.message || 'Error de conexión';
        errEl.classList.remove('hidden');
    } finally {
        btn.textContent = '💾 Guardar y relanzar análisis IA';
        btn.disabled = false;
        btn.style.opacity = '1';
    }
}
