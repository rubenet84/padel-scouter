/**
 * player_matches.js — Match CRUD Lifecycle
 *
 * PR #8A — Extract from player_detail.html inline script.
 * Script clásico (no module). Usa window.state, window.DOM, y funciones
 * de player_api.js como globales.
 *
 * Responsabilidad: ciclo de vida completo de partidos (CRUD) y torneos.
 *
 * Dependencias:
 *   - window.state (PlayerState desde player_detail.js)
 *   - window.DOM (referencias DOM desde player_detail.js)
 *   - apiSaveMatch / apiDeleteMatch (bridged desde player_api.js)
 *   - updateMatch, fetchPlayerStats, fetchMatches, fetchAllPlayers,
 *     fetchTournaments, createTournament, updateTournament, deleteTournamentApi
 *     (desde player_api.js)
 *   - getTournamentNameById (desde player_utils.js)
 *   - renderTournaments (desde tournament_renderer.js)
 *   - filterMatchesBySearch (desde player_search.js)
 *   - renderFullMatchHistory (desde match_renderer.js)
 */

// ── Match filter state ──────────────────────────────────────────
var currentFilter = 'all';

// ═══════════════════════════════════════════════════════════════
// 1. VALIDATION
// ═══════════════════════════════════════════════════════════════

function validateResultString(result) {
    if (!result) return { valid: false, msg: 'Resultado vacío' };
    const parts = result.trim().split(/\s+/).filter(Boolean);
    if (parts.length !== 2 && parts.length !== 3) {
        return { valid: false, msg: "Debe tener 2 o 3 sets (ej: '6-4 6-3' o '6-4 3-6 6-1')" };
    }
    let winsA = 0, winsB = 0;
    for (const token of parts) {
        const m = token.match(/^(\d+)-(\d+)$/);
        if (!m) return { valid: false, msg: `Formato de set inválido: ${token}` };
        const a = parseInt(m[1], 10), b = parseInt(m[2], 10);
        if (a === b) return { valid: false, msg: `Set empatado no válido: ${token}` };
        if (a < 0 || b < 0) return { valid: false, msg: `Puntuación inválida: ${token}` };

        const high = Math.max(a, b);
        const low = Math.min(a, b);
        const isValidSet = (high === 7 && (low === 5 || low === 6)) || (high === 6 && low <= 4);
        if (!isValidSet) {
            return { valid: false, msg: `Set inválido según FIP 2026: ${token}. Valores válidos: 6-0 a 6-4, 7-5, 7-6, 6-7` };
        }

        if (a > b) winsA++; else winsB++;
    }
    if (parts.length === 2) {
        if (!(winsA === 2 || winsB === 2)) {
            return { valid: false, msg: 'Si hay 2 sets, uno debe ganar ambos (ej: 6-2 6-2)' };
        }
    } else {
        if (!(winsA === 2 || winsB === 2)) {
            return { valid: false, msg: "En 3 sets alguien debe ganar 2 sets (ej: '6-2 2-6 6-4')" };
        }
    }
    return { valid: true, winsA, winsB, winner: winsA > winsB ? 'A' : 'B' };
}

// ═══════════════════════════════════════════════════════════════
// 2. COMPUTED STATS
// ═══════════════════════════════════════════════════════════════

async function renderComputedStats(pid) {
    try {
        const stats = await fetchPlayerStats(pid);
        const D = window.DOM;

        D.statTorneos().textContent = stats.torneos;
        D.statTorneos().nextElementSibling.textContent = 'Torneos';
        D.statWinrate().textContent = stats.win_rate.toFixed(1) + '%';
        D.statWinrate().nextElementSibling.textContent = 'victorias';
        D.statFep().textContent = stats.fep_points.toLocaleString();
        D.statFep().nextElementSibling.textContent = 'Pts FEP';

        const compPct = Math.min(stats.win_rate, 100);
        D.barComp().style.width = compPct + '%';
        D.barCompVal().textContent = compPct.toFixed(1) + '%';
    } catch (e) {
        console.warn('renderComputedStats error:', e);
        const D = window.DOM;
        D.statTorneos().textContent = '—';
        D.statWinrate().textContent = '—';
        D.statFep().textContent = '—';
    }
}

// ═══════════════════════════════════════════════════════════════
// 3. MATCH FORM HELPERS
// ═══════════════════════════════════════════════════════════════

function resetMatchForm() {
    const D = window.DOM;
    const formFields = [
        'm-tipo', 'm-rival', 'm-pareja-rival', 'm-resultado', 'm-ganado', 'm-scoring',
        'm-torneo-select', 'm-ronda', 'm-notas', 'm-date',
        'm-partner-select', 'm-partner-name'
    ];
    formFields.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.value = '';
        if (el.tagName === 'SELECT') el.selectedIndex = 0;
    });

    // Reset partner section (unlock, re-enable, hide text input)
    unlockPartnerSection();

    // Hide inline tournament form
    const newForm = D.newTournamentForm?.();
    if (newForm) newForm.classList.add('hidden');

    // Hide tournament admin row (edit/delete) until user selects a tournament
    const adminRow = D.tournamentAdminRow?.();
    if (adminRow) adminRow.classList.add('hidden');
    const editForm = D.editTournamentForm?.();
    if (editForm) editForm.classList.add('hidden');

    const error = D.matchError?.();
    if (error) {
        error.textContent = '';
        error.classList.add('hidden');
    }

    const tipo = D.mTipo?.();
    if (tipo) {
        tipo.value = 'amistoso';
        tipo.disabled = false;
    }
    const titleEl = D.matchModalTitle?.();
    if (titleEl) titleEl.textContent = '\uD83D\uDCCB Nuevo partido';

    // Re-enable and show tournament-related elements
    const torneoSelect = D.mTorneoSelect?.();
    if (torneoSelect) torneoSelect.disabled = false;
    const rondaSel = D.mRonda?.();
    if (rondaSel) rondaSel.disabled = false;
    const torneoSection = D.torneoSelectSection?.();
    if (torneoSection) torneoSection.classList.remove('hidden');

    const editName = D.torneoEditName?.();
    if (editName) editName.classList.add('hidden');

    toggleTorneo();
}

function toggleTorneo() {
    const tipo = document.getElementById('m-tipo').value;
    const torneoFields = document.getElementById('torneo-fields');
    const amistosoRivalField = document.getElementById('amistoso-rival-field');
    if (tipo === 'torneo') {
        torneoFields.classList.remove('hidden');
        if (amistosoRivalField) amistosoRivalField.classList.add('hidden');
    } else {
        torneoFields.classList.add('hidden');
        if (amistosoRivalField) amistosoRivalField.classList.remove('hidden');
        const newForm = document.getElementById('new-tournament-form');
        if (newForm) newForm.classList.add('hidden');
        unlockPartnerSection();
    }
}

async function openMatchModal() {
    resetMatchForm();
    // Load partner players list
    await loadPartnerPlayers();
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('m-date').value = today;
    document.getElementById('match-modal').classList.remove('hidden');
}

// ═══════════════════════════════════════════════════════════════
// 4. PARTNER / COMPAÑERO
// ═══════════════════════════════════════════════════════════════

async function loadPartnerPlayers() {
    try {
        const players = await fetchAllPlayers();
        const select = document.getElementById('m-partner-select');
        if (!select) return;
        const currentValue = select.value;
        select.innerHTML = '<option value="">— Seleccionar jugador —</option>';
        players.forEach(p => {
            if (p.id === playerId) return;
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name + ' (' + p.category + ')';
            if (p.id === currentValue) opt.selected = true;
            select.appendChild(opt);
        });
        if (currentValue) select.value = currentValue;
    } catch (e) {
        console.warn('loadPartnerPlayers error:', e);
    }
}

function onPartnerSelect() {
    const select = document.getElementById('m-partner-select');
    const input = document.getElementById('m-partner-name');
    if (!select || !input) return;
    if (select.value) {
        input.value = '';
    }
}

function lockPartnerForTournament(partnerName) {
    const select = document.getElementById('m-partner-select');
    const input = document.getElementById('m-partner-name');
    const section = document.getElementById('partner-section');
    if (!select || !input || !section) return;
    select.disabled = true;
    input.disabled = true;
    const existingLock = document.getElementById('partner-locked-display');
    if (!existingLock) {
        const display = document.createElement('div');
        display.id = 'partner-locked-display';
        display.className = 'flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm text-white';
        display.style.cssText = 'background:#0A0A0F;border:1px solid rgba(168,85,247,0.2);opacity:0.7;';
        display.innerHTML = `<span>\uD83D\uDD12 ${escapeHtml(partnerName)}</span>`;
        const flexContainer = select.parentElement;
        flexContainer.classList.add('hidden');
        flexContainer.parentElement.insertBefore(display, flexContainer);
    }
}

function unlockPartnerSection() {
    const select = document.getElementById('m-partner-select');
    const input = document.getElementById('m-partner-name');
    if (select) { select.disabled = false; select.value = ''; }
    if (input) { input.disabled = false; input.value = ''; }
    const lockedDisplay = document.getElementById('partner-locked-display');
    if (lockedDisplay) lockedDisplay.remove();
    const flexContainer = select ? select.parentElement : null;
    if (flexContainer) flexContainer.classList.remove('hidden');
}

// ═══════════════════════════════════════════════════════════════
// 5. TOURNAMENT CRUD
// ═══════════════════════════════════════════════════════════════

async function loadTournaments() {
    try {
        const tournaments = await fetchTournaments(playerId);
        state.tournaments = tournaments;
        renderTournaments(tournaments, 'm-torneo-select');
    } catch (e) {
        console.warn('loadTournaments error:', e);
    }
}

function loadTournamentFilterOptions() {
    filterMatchHistory();
}

function showNewTournamentForm() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('m-tournament-date').value = today;
    document.getElementById('m-tournament-fep').value = '';
    document.getElementById('m-tournament-name').value = '';
    document.getElementById('new-tournament-error').classList.add('hidden');
    document.getElementById('new-tournament-form').classList.remove('hidden');
    const editForm = document.getElementById('edit-tournament-form');
    if (editForm) editForm.classList.add('hidden');
    document.getElementById('edit-tournament-error')?.classList.add('hidden');
    const adminRow = document.getElementById('tournament-admin-row');
    if (adminRow) adminRow.classList.add('hidden');
}

function cancelNewTournament() {
    document.getElementById('new-tournament-form').classList.add('hidden');
}

async function createTournamentInline() {
    const D = window.DOM;
    const errEl = D.newTournamentError?.();
    if (!errEl) return;
    errEl.classList.add('hidden');

    const name = (D.mTournamentName?.()?.value || '').trim();
    const date = D.mTournamentDate?.()?.value || '';
    const fepRaw = D.mTournamentFep?.()?.value || '';
    const fepPoints = fepRaw ? parseInt(fepRaw, 10) : 0;

    if (!name || name.length < 2) {
        errEl.textContent = 'El nombre del torneo debe tener al menos 2 caracteres.';
        errEl.classList.remove('hidden');
        return;
    }
    if (name.length > 200) {
        errEl.textContent = 'El nombre del torneo no puede superar los 200 caracteres.';
        errEl.classList.remove('hidden');
        return;
    }
    if (!date) {
        errEl.textContent = 'La fecha del torneo es requerida.';
        errEl.classList.remove('hidden');
        return;
    }

    const dup = state.tournaments.find(t => t.name === name && t.date === date);
    if (dup) {
        cancelNewTournament();
        const select = D.mTorneoSelect?.();
        if (select) {
            select.value = dup.id;
            onTournamentSelect();
            filterMatchHistory();
        }
        showToast('\u2705 Torneo ya existente — seleccionado');
        return;
    }

    try {
        const tournament = await createTournament({
            name: name,
            date: date,
            fep_points: fepPoints,
            player_id: playerId
        });

        cancelNewTournament();

        const select = D.mTorneoSelect?.();
        if (select) {
            const opt = document.createElement('option');
            opt.value = tournament.id;
            const dateStr = new Date(tournament.date).toLocaleDateString('es-ES');
            opt.textContent = `\uD83C\uDFC6 ${tournament.name} — ${dateStr}`;
            select.appendChild(opt);
            select.value = tournament.id;
        }
        state.tournaments.push(tournament);
        onTournamentSelect();
        filterMatchHistory();

        showToast('\u2705 Torneo creado', 'success');
    } catch (e) {
        errEl.textContent = e.message || 'Error de conexión al crear torneo';
        errEl.classList.remove('hidden');
    }
}

function getSelectedTournament() {
    const select = document.getElementById('m-torneo-select');
    const tid = select ? select.value : '';
    if (!tid) return null;
    return state.tournaments.find(t => t.id === tid) || null;
}

function onTournamentSelect() {
    const D = window.DOM;
    D.matchError?.()?.classList.add('hidden');

    const editForm = D.editTournamentForm?.();
    if (editForm) editForm.classList.add('hidden');
    const newForm = D.newTournamentForm?.();
    if (newForm) newForm.classList.add('hidden');
    D.newTournamentError?.()?.classList.add('hidden');

    const t = getSelectedTournament();
    const adminRow = D.tournamentAdminRow?.();
    if (!t) {
        if (adminRow) adminRow.classList.add('hidden');
        return;
    }
    const nameEl = document.getElementById('tournament-admin-name');
    if (nameEl) {
        const dateStr = new Date(t.date).toLocaleDateString('es-ES');
        const fepText = t.fep_points ? ` \u00B7 ${t.fep_points} pts` : '';
        nameEl.textContent = `\uD83C\uDFC6 ${t.name}${fepText} — ${dateStr}`;
    }
    if (adminRow) adminRow.classList.remove('hidden');

    const isEditing = D.btnSaveMatch?.()?.dataset?.matchId;
    if (!isEditing) {
        unlockPartnerSection();
        const existingMatch = (state.matches || []).find(m =>
            m.tournament_id === t.id &&
            (m.partner_id || m.partner_nombre)
        );
        if (existingMatch) {
            const select = D.mPartnerSelect?.();
            const input = D.mPartnerName?.();
            if (existingMatch.partner_id && select) {
                select.value = existingMatch.partner_id;
                onPartnerSelect();
            } else if (existingMatch.partner_nombre && input) {
                input.value = existingMatch.partner_nombre;
            }
            lockPartnerForTournament(existingMatch.partner_nombre || 'Compa\u00F1ero');
        }
    }
}

function showTournamentEditForm() {
    const t = getSelectedTournament();
    if (!t) return;
    const D = window.DOM;
    const nameEl = D.eTournamentName?.();
    if (nameEl) nameEl.value = t.name;
    const dateEl = D.eTournamentDate?.();
    if (dateEl) dateEl.value = t.date;
    const fepEl = D.eTournamentFep?.();
    if (fepEl) fepEl.value = t.fep_points || '';
    D.editTournamentError?.()?.classList.add('hidden');
    D.editTournamentForm?.()?.classList.remove('hidden');
    const newForm = D.newTournamentForm?.();
    if (newForm) newForm.classList.add('hidden');
    D.newTournamentError?.()?.classList.add('hidden');
}

function cancelTournamentEdit() {
    const D = window.DOM;
    D.editTournamentForm?.()?.classList.add('hidden');
    D.editTournamentError?.()?.classList.add('hidden');
}

async function saveTournamentEdit() {
    const t = getSelectedTournament();
    if (!t) return;
    const D = window.DOM;
    const errEl = D.editTournamentError?.();
    if (!errEl) return;
    errEl.classList.add('hidden');

    const name = (D.eTournamentName?.()?.value || '').trim();
    const date = D.eTournamentDate?.()?.value || '';
    const fepRaw = D.eTournamentFep?.()?.value || '';
    const fepPoints = fepRaw ? parseInt(fepRaw, 10) : null;

    if (!name || name.length < 2) {
        errEl.textContent = 'El nombre debe tener al menos 2 caracteres.';
        errEl.classList.remove('hidden');
        return;
    }
    if (name.length > 200) {
        errEl.textContent = 'El nombre no puede superar 200 caracteres.';
        errEl.classList.remove('hidden');
        return;
    }
    if (!date) {
        errEl.textContent = 'La fecha es requerida.';
        errEl.classList.remove('hidden');
        return;
    }

    const body = { name, date, fep_points: fepPoints };

    try {
        await updateTournament(t.id, body);
        cancelTournamentEdit();
        await loadTournaments();
        filterMatchHistory();
        const select = D.mTorneoSelect?.();
        if (select) select.value = t.id;
        onTournamentSelect();
        renderComputedStats(playerId);

        const historyModal = document.getElementById('match-history-modal');
        if (historyModal && !historyModal.classList.contains('hidden')) {
            await loadMatches();
            renderFullMatchHistory(state.matches);
        } else {
            await loadMatches();
        }
        showToast('\u2705 Torneo actualizado', 'success');
    } catch (e) {
        errEl.textContent = e.message || 'Error de conexión al actualizar torneo';
        errEl.classList.remove('hidden');
    }
}

async function deleteSelectedTournament() {
    const t = getSelectedTournament();
    if (!t) return;

    if (!confirm(`\u00BFEst\u00E1s seguro de eliminar el torneo "${t.name}"?\n\nEsta acci\u00F3n no se puede deshacer.`)) {
        return;
    }

    try {
        await deleteTournamentApi(t.id);
        const select = document.getElementById('m-torneo-select');
        if (select) {
            const opt = select.querySelector(`option[value="${t.id}"]`);
            if (opt) opt.remove();
            select.value = '';
        }
        state.tournaments = state.tournaments.filter(x => x.id !== t.id);
        onTournamentSelect();
        filterMatchHistory();
        showToast('\uD83D\uDDD1\uFE0F Torneo eliminado', 'success');
    } catch (e) {
        showToast(e.message || 'Error al eliminar torneo', 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
// 6. MATCH FILTER
// ═══════════════════════════════════════════════════════════════

async function onMatchFilterChange() {
    currentFilter = document.getElementById('match-filter').value;
    await loadMatches();
}

async function loadMatches() {
    const filter = currentFilter || 'all';
    try {
        const matches = await fetchMatches(playerId, filter);
        allServerMatches = matches;
        filterMatchesBySearch();
    } catch (e) {
        console.warn('loadMatches error:', e);
    }
}

// ═══════════════════════════════════════════════════════════════
// 7. MATCH CRUD
// ═══════════════════════════════════════════════════════════════

async function saveMatch() {
    const D = window.DOM;
    const tipoEl = D.mTipo?.();
    const tipo = tipoEl ? tipoEl.value : '';
    const resultadoEl = D.mResultado?.();
    const resultado = resultadoEl ? String(resultadoEl.value || '').trim().replace(/\s+/g, ' ') : '';
    const ganadoEl = D.mGanado?.();
    const ganado = ganadoEl ? (ganadoEl.value === 'true') : false;
    const errEl = D.matchError?.();
    if (errEl) errEl.classList.add('hidden');

    let rival = '';
    let tournamentId = null;
    let ronda = null;

    if (tipo === 'torneo') {
        const torneoSelect = D.mTorneoSelect?.();
        tournamentId = torneoSelect ? torneoSelect.value : '';
        const pareja = (D.mParejaRival?.()?.value || '').trim();
        ronda = D.mRonda?.()?.value || null;

        if (!tournamentId) {
            if (errEl) {
                errEl.textContent = 'Selecciona un torneo de la lista';
                errEl.classList.remove('hidden');
            }
            console.warn('saveMatch validation failed: torneo requerido');
            return;
        }

        rival = pareja;
    } else {
        const rivalEl = D.mRival?.();
        rival = rivalEl ? String(rivalEl.value || '').trim() : '';
    }

    // OWASP: validate name max length
    if (rival.length > 200) {
        if (errEl) {
            errEl.textContent = 'El nombre del rival es demasiado largo (máx 200 caracteres)';
            errEl.classList.remove('hidden');
        }
        return;
    }

    if (!rival || !resultado) {
        if (errEl) {
            errEl.textContent = 'Rellena el rival y el resultado';
            errEl.classList.remove('hidden');
        }
        console.warn('saveMatch validation failed', { rival, resultado });
        return;
    }

    // ── Validación de resultado ──
    const notasValue = (D.mNotas?.()?.value || '').trim();
    const esLesion = hasLesionNote(notasValue);

    if (!esLesion) {
        const vr = validateResultString(resultado);
        if (!vr.valid) {
            if (errEl) { errEl.textContent = vr.msg; errEl.classList.remove('hidden'); }
            console.warn('saveMatch result invalid', vr.msg);
            return;
        }

        const expectedWinner = vr.winner === 'A';
        if (expectedWinner !== ganado) {
            if (errEl) {
                errEl.textContent = ganado
                    ? 'El resultado no indica que el jugador haya ganado dos sets.'
                    : 'El resultado indica que el jugador ganó dos sets.';
                errEl.classList.remove('hidden');
            }
            console.warn('saveMatch winner mismatch', { resultado, ganado, vr });
            return;
        }
    }

    // ── Validaciones de torneo ──
    const btn = D.btnSaveMatch?.();
    if (tipo === 'torneo' && tournamentId && ronda) {
        const matchId = btn?.dataset?.matchId;
        const currentIdx = getRoundIndex(ronda);

        // Regla 1: si hay una derrota en ronda INFERIOR (eliminación), no se puede pasar de esa ronda
        if (!matchId && currentIdx >= 0) {
            const lowerLoss = state.matches.find(m =>
                m.tournament_id === tournamentId &&
                m.ganado === false &&
                getRoundIndex(m.ronda) >= 0 &&
                getRoundIndex(m.ronda) < currentIdx
            );
            if (lowerLoss) {
                if (errEl) {
                    errEl.textContent = `Este jugador ya perdió en ${lowerLoss.ronda}. No puede haber partidos en rondas posteriores.`;
                    errEl.classList.remove('hidden');
                }
                return;
            }
        }

        // Regla 2: si es derrota, no puede haber partidos GANADOS en rondas superiores
        if (ganado === false && currentIdx >= 0) {
            const higherWins = state.matches.filter(m =>
                m.tournament_id === tournamentId &&
                m.ganado === true &&
                getRoundIndex(m.ronda) >= 0 &&
                getRoundIndex(m.ronda) > currentIdx &&
                m.id != matchId
            );
            if (higherWins.length > 0) {
                const rounds = [...new Set(higherWins.map(m => m.ronda))].join(', ');
                if (errEl) {
                    errEl.textContent = `No se puede marcar como derrota porque hay partidos ganados en rondas superiores: ${rounds}. Elimina primero esos partidos.`;
                    errEl.classList.remove('hidden');
                }
                return;
            }
        }

        // Regla 3: no duplicar ronda en el mismo torneo
        const dup = state.matches.find(m =>
            m.tournament_id === tournamentId &&
            m.ronda === ronda &&
            m.id != matchId
        );
        if (dup) {
            if (errEl) {
                errEl.textContent = `Ya existe un partido en ${ronda} para este torneo. Solo se puede editar o eliminar.`;
                errEl.classList.remove('hidden');
            }
            return;
        }
    }

    // ── Validación de fecha ──
    const fechaPartido = D.mDate?.()?.value;
    if (fechaPartido) {
        const fpDate = new Date(fechaPartido + 'T12:00:00');
        fpDate.setHours(0, 0, 0, 0);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (fpDate > today) {
            if (errEl) {
                const parts = fechaPartido.split('-');
                const fechaDisplay = `${parts[2]}-${parts[1]}-${parts[0]}`;
                errEl.textContent = `La fecha del partido (${fechaDisplay}) no puede ser posterior a hoy. Corrige la fecha para continuar.`;
                errEl.classList.remove('hidden');
            }
            return;
        }

        if (fpDate.getFullYear() < today.getFullYear() - 2) {
            if (!confirm(`La fecha ${fechaPartido} parece muy antigua. ¿Estás seguro de que es correcta?`)) {
                return;
            }
        }
    }

    if (btn) {
        btn.textContent = '\u23F3 Guardando...';
        btn.disabled = true;
    }

    try {
        const matchId = btn?.dataset?.matchId;
        const partnerSelect = D.mPartnerSelect?.();
        const partnerInput = D.mPartnerName?.();
        const selfPartnerId = btn?.dataset?.selfPartnerId || null;
        const body = {
            rival_nombre: rival,
            resultado: resultado,
            ganado: ganado,
            tournament_id: tipo === 'torneo' ? tournamentId : null,
            ronda: tipo === 'torneo' ? ronda : null,
            partner_id: selfPartnerId || (partnerSelect ? (partnerSelect.value || null) : null),
            partner_nombre: selfPartnerId ? null : (partnerInput ? (partnerInput.value.trim() || null) : null),
            scoring_method: D.mScoring?.()?.value || 'con_ventaja',
            notes: (D.mNotas?.()?.value || '').trim() || null,
            fecha_partido: D.mDate?.()?.value || null,
        };

        if (matchId) {
            await updateMatch(matchId, playerId, body);
        } else {
            await apiSaveMatch(playerId, body);
        }

        closeMatchModal();
        if (btn) {
            btn.dataset.matchId = '';
            btn.dataset.selfPartnerId = '';
            btn.textContent = '\uD83D\uDCBE Guardar partido';
        }
        await loadMatches();
        renderComputedStats(playerId);
    } catch (e) {
        console.error('saveMatch exception', e);
        if (errEl) {
            errEl.textContent = e.message || 'Error de conexión';
            errEl.classList.remove('hidden');
        }
    } finally {
        if (btn) {
            btn.textContent = '\uD83D\uDCBE Guardar partido';
            btn.disabled = false;
        }
    }
}

async function openEditMatchModal(matchId) {
    if (!matchId || !playerId || !token) {
        alert('Error: información del jugador faltante');
        return;
    }

    closeMatchHistoryModal();

    try {
        const allMatches = await fetchMatches(playerId);
        const match = allMatches.find(m => m.id == matchId);
        if (!match) {
            alert('Partido no encontrado');
            return;
        }

        const D = window.DOM;
        const isTorneo = match.tournament_id || (match.torneo && match.torneo.trim() !== '');
        const mTipo = D.mTipo?.();
        if (mTipo) {
            mTipo.value = isTorneo ? 'torneo' : 'amistoso';
            mTipo.disabled = true;
        }
        const titleEl = D.matchModalTitle?.();
        if (titleEl) titleEl.textContent = '\u270F\uFE0F Modificar partido';

        if (isTorneo) {
            const torneoSection = D.torneoSelectSection?.();
            if (torneoSection) torneoSection.classList.add('hidden');

            if (match.tournament_id) {
                const select = D.mTorneoSelect?.();
                if (select) {
                    select.value = match.tournament_id;
                    select.disabled = true;
                    onTournamentSelect();
                }
            }

            const adminRow = D.tournamentAdminRow?.();
            if (adminRow) adminRow.classList.add('hidden');

            const tName = getTournamentNameById(match.tournament_id, state.tournaments) || match.torneo || '';
            const editSelect = D.torneoEditNameSelect?.();
            if (editSelect) {
                editSelect.innerHTML = `<option>\uD83C\uDFC6 ${tName}</option>`;
            }
            const editName = D.torneoEditName?.();
            if (editName) editName.classList.remove('hidden');

            const rondaEl = D.mRonda?.();
            if (rondaEl && match.ronda) rondaEl.value = match.ronda;

            const parejaEl = D.mParejaRival?.();
            if (parejaEl) parejaEl.value = match.rival_nombre || '';

            const rivalEl = D.mRival?.();
            if (rivalEl) rivalEl.value = '';
        } else {
            const rivalEl = D.mRival?.();
            if (rivalEl && match.rival_nombre) rivalEl.value = match.rival_nombre;
        }

        // ── Partner / Compañero population ──
        await loadPartnerPlayers();
        const partnerSelect = D.mPartnerSelect?.();
        const partnerInput = D.mPartnerName?.();
        if (match.partner_id && partnerSelect) {
            if (match.partner_id === playerId) {
                // Soy el compañero — guardar ID para preservarlo al guardar
                const btn = D.btnSaveMatch?.();
                if (btn) btn.dataset.selfPartnerId = match.partner_id;
                if (partnerInput) partnerInput.value = match.partner_nombre || 'Yo';
                partnerSelect.value = '';
            } else {
                partnerSelect.value = match.partner_id;
                if (partnerInput) partnerInput.value = '';
                onPartnerSelect();
            }
        } else if (match.partner_nombre && partnerInput) {
            partnerInput.value = match.partner_nombre;
            if (partnerSelect) partnerSelect.value = '';
        }

        if (isTorneo) {
            const pName = match.partner_nombre || 'Compa\u00F1ero';
            lockPartnerForTournament(pName);
        }

        toggleTorneo();

        const resultadoEl = D.mResultado?.();
        if (resultadoEl) resultadoEl.value = match.resultado || '';
        const ganadoEl = D.mGanado?.();
        if (ganadoEl) ganadoEl.value = match.ganado ? 'true' : 'false';
        const scoringEl = D.mScoring?.();
        if (scoringEl) scoringEl.value = match.scoring_method || 'con_ventaja';
        const notasEl = D.mNotas?.();
        if (notasEl) notasEl.value = match.notes || '';
        const dateEl = D.mDate?.();
        if (dateEl) dateEl.value = (match.played_at || '').split('T')[0];

        // Store the matchId for update
        const btn = D.btnSaveMatch?.();
        if (btn) {
            btn.dataset.matchId = matchId;
            btn.textContent = '\u270F\uFE0F Actualizar partido';
        }

        // Clear any previous errors
        const errEl = D.matchError?.();
        if (errEl) errEl.classList.add('hidden');

        // Open modal
        const modal = D.matchModal?.();
        if (modal) modal.classList.remove('hidden');
    } catch (e) {
        console.error('openEditMatchModal error:', e);
        alert('Error al cargar el partido');
    }
}

async function deleteMatch(matchId) {
    if (!matchId || !playerId || !token) {
        alert('Error: información del jugador faltante');
        return;
    }

    const confirmed = confirm('¿Deseas eliminar el partido? Esta acción no se puede deshacer.');
    if (!confirmed) return;

    try {
        await apiDeleteMatch(matchId, playerId);
        await loadMatches();
        renderComputedStats(playerId);
        const historyModal = document.getElementById('match-history-modal');
        if (historyModal && !historyModal.classList.contains('hidden')) {
            renderFullMatchHistory(state.matches);
        }
    } catch (e) {
        console.error('deleteMatch error:', e);
        alert(e.message || 'Error al eliminar el partido');
    }
}

// ═══════════════════════════════════════════════════════════════
// 8. INIT — Bind save button
// ═══════════════════════════════════════════════════════════════

(function bindSaveMatchButton() {
    const btn = document.getElementById('btn-save-match');
    if (!btn) { console.warn('btn-save-match not found when binding saveMatch'); return; }
    btn.type = 'button';
    btn.addEventListener('click', function (e) { e.preventDefault(); saveMatch(); });
})();
