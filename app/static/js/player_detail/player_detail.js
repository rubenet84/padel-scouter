/**
 * player_detail.js
 *
 * Entry point for the player detail page.
 * PR #3 — Bridge module. Calls existing global functions from old inline script.
 *
 * Restricciones:
 * - No define funciones de render/CRUD/analytics
 * - Solo orquesta: carga estado, llama a funciones existentes
 * - Las funciones existentes viven en el bloque <script> clásico
 */

import { state } from './player_state.js';
import { DOM } from './player_dom.js';

// TEMP: Expuesto durante el refactor para mantener compatibilidad
// con el JS clásico inline que aún no puede importar módulos ES.
// Las funciones legacy acceden a state a través de window.state.
// Se eliminará en PR #8 cuando desaparezcan las referencias legacy.
window.state = state;

// TEMP: Expuesto para player_render.js (classic script) durante la migración.
// Se eliminará en PR #8 cuando player_render.js migre a módulo ES.
window.DOM = DOM;

export function initPlayerDetail() {
    const playerId = window.location.pathname.split('/').pop();
    state.playerId = playerId;

    // Call existing global functions (defined in classic <script> block)
    // loadPlayer() internally calls loadMatches() at the end
    loadPlayer();
    loadTournaments().then(() => {
        if (typeof loadTournamentFilterOptions === 'function') {
            loadTournamentFilterOptions();
        }
        if (typeof setSortMode === 'function') {
            setSortMode('date-desc');
        }
    });
}
