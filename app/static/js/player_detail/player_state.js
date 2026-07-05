/**
 * player_state.js
 *
 * Single source of truth for player detail data.
 * PR #3 — Infrastructure only. No getters/setters yet.
 *
 * Restricciones:
 * - No DOM
 * - No fetch
 * - No eventos
 * - Solo estado
 */

class PlayerState {
    constructor() {
        this.playerId = null;
        this.player = null;
        this.matches = [];
        this.tournaments = [];
        this.players = [];
    }
}

export const state = new PlayerState();
