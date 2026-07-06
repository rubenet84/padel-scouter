/**
 * tournament_renderer.js
 *
 * Tournament rendering — SOLO render, sin datos/API/CRUD.
 * PR #6B — Extracted from player_detail.html inline script.
 *
 * Restricciones:
 * - No fetch, no API calls
 * - Solo renderiza; no carga ni guarda datos
 * - Accede al DOM via document.getElementById
 * - Script clásico (no module)
 */

// ── Render Tournament Dropdown ───────────────────────────────
function renderTournaments(tournaments, selectElementId) {
    const select = document.getElementById(selectElementId);
    if (!select) return;
    // Keep the first placeholder option
    select.innerHTML = '<option value="">— Seleccionar —</option>';
    (tournaments || []).forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        const dateStr = new Date(t.date).toLocaleDateString('es-ES');
        opt.textContent = `🏆 ${t.name} — ${dateStr}`;
        select.appendChild(opt);
    });
}
