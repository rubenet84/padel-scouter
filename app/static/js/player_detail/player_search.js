/**
 * player_search.js
 *
 * Match search and filter logic.
 * PR #5 — Extracted from player_detail.html inline script.
 *
 * Restricciones:
 * - No DOM (except filterMatchesBySearch which reads input)
 * - No fetch
 * - Solo lógica de búsqueda y filtrado
 */

// ── Match history filter with search ──────────────────────────
var allServerMatches = []; // Full matches from server (before search filter)
let searchedMatches = null; // Filtered results when search bar has text

function filterMatchesBySearch() {
    const query = document.getElementById('mh-filter-search').value.toLowerCase().trim();
    if (!query) {
        searchedMatches = null;
        renderMatches(allServerMatches);
        return;
    }
    const terms = query.split(/\s+/).filter(t => t);
    const filtered = allServerMatches.filter(m => {
        const rival = (m.rival_nombre || '').toLowerCase();
        const playerName = (m.player1_name || '').toLowerCase();
        const d = new Date(m.played_at);
        // Componentes de fecha
        const dia   = d.getDate();
        const dia2  = String(dia).padStart(2, '0');
        const mesC  = d.toLocaleDateString('es-ES', {month:'short'}).toLowerCase().replace('.',''); // "jul"
        const mesL  = d.toLocaleDateString('es-ES', {month:'long'}).toLowerCase();                 // "julio"
        const anio  = d.getFullYear();
        const anio2 = String(anio).slice(-2);
        // Fechas con barra
        const fBarra1 = `${dia}/${d.getMonth()+1}/${anio}`;         // "1/7/2026"
        const fBarra2 = `${dia2}/${String(d.getMonth()+1).padStart(2,'0')}/${anio}`;  // "01/07/2026"
        const fBarra3 = `${dia2}/${String(d.getMonth()+1).padStart(2,'0')}/${anio2}`; // "01/07/26"
        // Fechas con guion
        const fGuion1 = fBarra1.replace(/\//g, '-');
        const fGuion2 = fBarra2.replace(/\//g, '-');
        const fGuion3 = fBarra3.replace(/\//g, '-');
        // Fecha ISO
        const isoDate = (m.played_at || '').split('T')[0];          // "2026-07-01"
        // Día + mes corto
        const fc1 = `${dia} ${mesC}`;    // "1 jul"
        const fc2 = `${dia2} ${mesC}`;   // "01 jul"
        const fc3 = `${dia} ${mesC} ${anio}`;   // "1 jul 2026"
        const fc4 = `${dia2} ${mesC} ${anio}`;  // "01 jul 2026"
        const fc5 = `${dia} ${mesC} ${anio2}`;  // "1 jul 26"
        const fc6 = `${dia2} ${mesC} ${anio2}`; // "01 jul 26"
        // Día + mes largo
        const fl1 = `${dia} ${mesL}`;     // "1 julio"
        const fl2 = `${dia2} ${mesL}`;    // "01 julio"
        const fl3 = `${dia} ${mesL} ${anio}`;   // "1 julio 2026"
        const fl4 = `${dia2} ${mesL} ${anio}`;  // "01 julio 2026"
        const fl5 = `${dia} ${mesL} ${anio2}`;  // "1 julio 26"
        const fl6 = `${dia2} ${mesL} ${anio2}`; // "01 julio 26"
        // Con "de"
        const fDe1 = `${dia} de ${mesL} de ${anio}`;   // "1 de julio de 2026"
        const fDe2 = `${dia2} de ${mesL} de ${anio}`;  // "01 de julio de 2026"
        const fDe3 = `${dia} de ${mesL} de ${anio2}`;  // "1 de julio de 26"
        const fDe4 = `${dia2} de ${mesL} de ${anio2}`; // "01 de julio de 26"
        // Solo mes/año
        const soloAnio   = String(anio);
        const soloAnio2  = anio2;
        const soloMes    = mesL;
        const soloMesC   = mesC;
        const resultado    = (m.resultado || '').toLowerCase();
        const torneo       = getTournamentNameById(m.tournament_id, state.tournaments).toLowerCase();
        const rondaPal     = (m.ronda || '').toLowerCase();
        const ganado       = m.ganado ? 'victoria' : 'derrota';
        const notas        = (m.notes || '').toLowerCase();
        const lesion       = hasLesionNote(m.notes) ? 'lesion' : '';
        const partner      = (m.partner_nombre || '').toLowerCase();
        const scoring      = ((m.scoring_method || '').toString().toLowerCase() === 'con_ventaja' ? 'con ventaja' :
                              (m.scoring_method || '').toString().toLowerCase() === 'punto_oro' ? 'punto oro' :
                              (m.scoring_method || '').toString().toLowerCase() === 'star_point' ? 'star point' : '');
        const tipo         = m.tournament_id ? 'torneo' : 'amistoso';
        // Cada término debe aparecer en ALGÚN campo del mismo partido (AND).
        // Ronda se matchea como palabra completa para no mezclar "final" con "semifinal".
        const haystack = [rival, playerName, resultado, torneo, rondaPal, ganado, notas, lesion,
            partner, scoring, tipo,
            soloAnio, soloAnio2, soloMes, soloMesC,
            fBarra1, fBarra2, fBarra3,
            fGuion1, fGuion2, fGuion3,
            isoDate,
            fc1, fc2, fc3, fc4, fc5, fc6,
            fl1, fl2, fl3, fl4, fl5, fl6,
            fDe1, fDe2, fDe3, fDe4
        ];
        const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        return terms.every(t =>
            haystack.some(f => f.includes(t)) ||
            (rondaPal && new RegExp(`\\b${esc(t)}\\b`).test(rondaPal))
        );
    });
    searchedMatches = filtered.length > 0 ? filtered : null;
    if (filtered.length === 0 && allServerMatches.length > 0) {
        renderMatches(filtered, `Sin resultados para "${query}"`);
    } else if (filtered.length <= 3) {
        renderMatches(filtered);
    } else {
        renderMatches(filtered.slice(0, 3), null, filtered.length);
    }
}

function filterMatchHistory() {
    const select = document.getElementById('match-filter');
    const currentVal = select.value;
    select.innerHTML = '<option value="all">📋 Todos</option><option value="amistoso">🎾 Amistosos</option>';
    state.tournaments.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = `🏆 ${t.name}`;
        select.appendChild(opt);
    });
    if (currentVal && [...select.options].some(o => o.value === currentVal)) {
        select.value = currentVal;
    }
    onMatchFilterChange();
}
