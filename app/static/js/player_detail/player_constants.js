/**
 * player_constants.js
 *
 * Constants for player detail views.
 * PR #3 — Extracted from player_detail.html inline script.
 *
 * Restricciones:
 * - No DOM
 * - No fetch
 * - No estado
 * - No eventos
 * - Solo datos
 */

const CATEGORY_LEVELS = {
    'Iniciación':   { min: 1.0, max: 2.5,  group: 'Iniciación', color: '#22c55e', icon: '🟢' },
    '5ª Categoría': { min: 2.0, max: 3.0,  group: 'Intermedio', color: '#eab308', icon: '🟡' },
    '4ª Categoría': { min: 3.0, max: 3.75, group: 'Intermedio', color: '#eab308', icon: '🟡' },
    '3ª Categoría': { min: 3.75,max: 4.25, group: 'Intermedio', color: '#eab308', icon: '🟡' },
    '2ª Categoría': { min: 4.25,max: 4.75, group: 'Avanzado',  color: '#ef4444', icon: '🔴' },
    '1ª Categoría': { min: 4.75,max: 6.0,  group: 'Avanzado',  color: '#ef4444', icon: '🔴' },
    'Profesional':  { min: 6.0, max: 7.0,  group: 'Avanzado',  color: '#ef4444', icon: '🔴' },
};
