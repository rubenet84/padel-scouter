/**
 * player_dom.js
 *
 * Centralized DOM element references.
 * PR #3 — Infrastructure only. NOT wired into template yet.
 *
 * Restricciones:
 * - Solo DOM queries
 * - No estado
 * - No fetch
 * - No eventos
 * - Funciones flecha (evaluación perezosa)
 */

export const DOM = Object.freeze({
    // --- Player info ---
    playerName: () => document.getElementById('player-name'),
    breadcrumbName: () => document.getElementById('breadcrumb-name'),
    badgeCategory: () => document.getElementById('badge-category'),
    badgeSuggested: () => document.getElementById('badge-suggested'),
    avatarImg: () => document.getElementById('avatar-img'),
    avatarPlaceholder: () => document.getElementById('avatar-placeholder'),
    avatarInput: () => document.getElementById('avatar-input'),
    avatarSpinner: () => document.getElementById('avatar-spinner'),

    // --- Stats bars ---
    barTecnica: () => document.getElementById('bar-tecnica'),
    barTecnicaVal: () => document.getElementById('bar-tecnica-val'),
    barFisico: () => document.getElementById('bar-fisico'),
    barFisicoVal: () => document.getElementById('bar-fisico-val'),
    barMental: () => document.getElementById('bar-mental'),
    barMentalVal: () => document.getElementById('bar-mental-val'),
    barComp: () => document.getElementById('bar-comp'),
    barCompVal: () => document.getElementById('bar-comp-val'),

    // --- Stat values ---
    valRemate: () => document.getElementById('val-remate'),
    valBandeja: () => document.getElementById('val-bandeja'),
    valVoleaDerecha: () => document.getElementById('val-volea_derecha'),
    valVoleaReves: () => document.getElementById('val-volea_reves'),

    // --- Power / Analysis ---
    powerDisplay: () => document.getElementById('power-display'),
    powerBar: () => document.getElementById('power-bar'),
    aiDescCard: () => document.getElementById('ai-desc-card'),
    aiDescription: () => document.getElementById('ai-description'),
    swSection: () => document.getElementById('sw-section'),
    strengthsList: () => document.getElementById('strengths-list'),
    weaknessesList: () => document.getElementById('weaknesses-list'),
    planCard: () => document.getElementById('plan-card'),
    improvementPlan: () => document.getElementById('improvement-plan'),
    noAnalysisCta: () => document.getElementById('no-analysis-cta'),

    // --- Radar ---
    radarChart: () => document.getElementById('radarChart'),

    // --- Golpe / Dragon Balls ---
    golpeCard: () => document.getElementById('golpe-card'),
    golpeNombre: () => document.getElementById('golpe-nombre'),
    golpeStatSub: () => document.getElementById('golpe-stat-sub'),
    golpeDescripcion: () => document.getElementById('golpe-descripcion'),
    nivelAmenazaBadge: () => document.getElementById('nivel-amenaza-badge'),
    nivelAmenazaText: () => document.getElementById('nivel-amenaza-text'),
    amenazaBar: () => document.getElementById('amenaza-bar'),
    dragonBallsContainer: () => document.getElementById('dragon-balls-container'),
    shenronSection: () => document.getElementById('shenron-section'),
    shenronContainer: () => document.getElementById('shenron-container'),
    shenronSvg: () => document.getElementById('shenron-svg'),
    mrsatanSection: () => document.getElementById('mrsatan-section'),
    gohanSection: () => document.getElementById('gohan-section'),
    goku4Section: () => document.getElementById('goku4-section'),
    gokuVideo: () => document.getElementById('goku-video'),

    // --- Match listing ---
    matchesSection: () => document.getElementById('matches-section'),
    matchesList: () => document.getElementById('matches-list'),
    matchFilter: () => document.getElementById('match-filter'),
    mhFilterSearch: () => document.getElementById('mh-filter-search'),
    matchHistoryList: () => document.getElementById('match-history-list'),

    // --- Match form ---
    matchModal: () => document.getElementById('match-modal'),
    matchModalTitle: () => document.getElementById('match-modal-title'),
    matchError: () => document.getElementById('match-error'),
    btnSaveMatch: () => document.getElementById('btn-save-match'),
    mDate: () => document.getElementById('m-date'),
    mTipo: () => document.getElementById('m-tipo'),
    mRival: () => document.getElementById('m-rival'),
    mResultado: () => document.getElementById('m-resultado'),
    mGanado: () => document.getElementById('m-ganado'),
    mNotas: () => document.getElementById('m-notas'),
    mRonda: () => document.getElementById('m-ronda'),
    mScoring: () => document.getElementById('m-scoring'),
    mTorneoSelect: () => document.getElementById('m-torneo-select'),
    mPartnerName: () => document.getElementById('m-partner-name'),
    mPartnerSelect: () => document.getElementById('m-partner-select'),
    mParejaRival: () => document.getElementById('m-pareja-rival'),
    partnerSection: () => document.getElementById('partner-section'),
    partnerLockedDisplay: () => document.getElementById('partner-locked-display'),
    amistosoRivalField: () => document.getElementById('amistoso-rival-field'),
    torneoFields: () => document.getElementById('torneo-fields'),
    torneoSelectSection: () => document.getElementById('torneo-select-section'),

    // --- Tournament form ---
    mTournamentName: () => document.getElementById('m-tournament-name'),
    mTournamentDate: () => document.getElementById('m-tournament-date'),
    mTournamentFep: () => document.getElementById('m-tournament-fep'),
    eTournamentName: () => document.getElementById('e-tournament-name'),
    eTournamentDate: () => document.getElementById('e-tournament-date'),
    eTournamentFep: () => document.getElementById('e-tournament-fep'),
    newTournamentForm: () => document.getElementById('new-tournament-form'),
    newTournamentError: () => document.getElementById('new-tournament-error'),
    editTournamentForm: () => document.getElementById('edit-tournament-form'),
    editTournamentError: () => document.getElementById('edit-tournament-error'),
    tournamentAdminName: () => document.getElementById('tournament-admin-name'),
    tournamentAdminRow: () => document.getElementById('tournament-admin-row'),
    torneoEditName: () => document.getElementById('torneo-edit-name'),
    torneoEditNameSelect: () => document.getElementById('torneo-edit-name-select'),

    // --- Edit modal ---
    editModal: () => document.getElementById('edit-modal'),
    editName: () => document.getElementById('edit-name'),
    editCategory: () => document.getElementById('edit-category'),
    editError: () => document.getElementById('edit-error'),
    btnSave: () => document.getElementById('btn-save'),

    // --- Modals ---
    statsModal: () => document.getElementById('stats-modal'),
    matchAnalyticsModal: () => document.getElementById('match-analytics-modal'),
    analyticsLoading: () => document.getElementById('analytics-loading'),
    analyticsContent: () => document.getElementById('analytics-content'),
    levelGuideModal: () => document.getElementById('level-guide-modal'),
    matchHistoryModal: () => document.getElementById('match-history-modal'),

    // --- Analytics content ---
    aTotalPartidos: () => document.getElementById('a-total-partidos'),
    aVictorias: () => document.getElementById('a-victorias'),
    aDerrotas: () => document.getElementById('a-derrotas'),
    aWinRate: () => document.getElementById('a-win-rate'),
    aTotalSets: () => document.getElementById('a-total-sets'),
    aSetsGanados: () => document.getElementById('a-sets-ganados'),
    aSetsPerdidos: () => document.getElementById('a-sets-perdidos'),
    aSetRatio: () => document.getElementById('a-set-ratio'),
    a2Sets: () => document.getElementById('a-2-sets'),
    a2SetsRatio: () => document.getElementById('a-2-sets-ratio'),
    a3Sets: () => document.getElementById('a-3-sets'),
    a3SetsRatio: () => document.getElementById('a-3-sets-ratio'),
    aTorneos: () => document.getElementById('a-torneos'),
    aAmistosos: () => document.getElementById('a-amistosos'),
    aMejorRondaRow: () => document.getElementById('a-mejor-ronda-row'),
    aMejorRonda: () => document.getElementById('a-mejor-ronda'),
    aRondasSection: () => document.getElementById('a-rondas-section'),
    aRondasList: () => document.getElementById('a-rondas-list'),
    aFaseMedia: () => document.getElementById('a-fase-media'),
    aScoringList: () => document.getElementById('a-scoring-list'),

    // --- State indicators ---
    loadingState: () => document.getElementById('loading-state'),
    errorState: () => document.getElementById('error-state'),
    mainContent: () => document.getElementById('main-content'),

    // --- Stats section ---
    statTorneos: () => document.getElementById('stat-torneos'),
    statWinrate: () => document.getElementById('stat-winrate'),
    statFep: () => document.getElementById('stat-fep'),

    // --- Edit ---
    btnAnalyze: () => document.getElementById('btn-analyze'),
});
