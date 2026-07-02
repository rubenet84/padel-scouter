"""Shared round constants and utilities for tournament round calculations.

Single source of truth for ROUND_ORDER, ROUND_WEIGHTS, and round-related
helper functions used across the domain and API layers.
"""

# ── Round hierarchy (lower index = earlier round, single-elimination) ──
ROUND_ORDER: list[str] = [
    "Fase de grupos",
    "32avos",
    "16avos",
    "Octavos",
    "Cuartos",
    "Semifinal",
    "Final",
]

# Puntos FEP por ronda (% del total del torneo)
ROUND_WEIGHTS: dict[str, float] = {
    "Fase de grupos": 0.0,
    "32avos":         0.1780,
    "16avos":         0.2373,
    "Octavos":        0.3164,
    "Cuartos":        0.4218,
    "Semifinal":      0.5625,
    "Final":          0.75,
}


def get_round_index(round_name: str) -> int:
    """Get the hierarchical index of a round name. Returns -1 if unknown."""
    try:
        return ROUND_ORDER.index(round_name)
    except ValueError:
        return -1


def best_round_info(matches: list) -> tuple[str | None, int, float]:
    """
    Analiza los partidos de un torneo y devuelve:
      (nombre_ronda, indice_ronda, peso)
    según la mejor ronda del jugador.

    1. Busca la ronda más alta con VICTORIA.
    2. Si ganó la Final → campeón (índice 6, peso 1.0).
    3. Si no hay victoria → ronda más alta alcanzada.
    """
    win_idx = -1
    reach_idx = -1

    for m in matches:
        ronda = (getattr(m, "ronda", None) or "").strip()
        if ronda in ROUND_ORDER:
            idx = ROUND_ORDER.index(ronda)
            if idx > reach_idx:
                reach_idx = idx
            if getattr(m, "ganado", False) and idx > win_idx:
                win_idx = idx

    if win_idx >= 0 and ROUND_ORDER[win_idx] == "Final":
        return ("Final", 6, 1.0)

    if win_idx >= 0:
        name = ROUND_ORDER[win_idx]
        return (name, win_idx, ROUND_WEIGHTS.get(name, 0.0))

    if reach_idx >= 0:
        name = ROUND_ORDER[reach_idx]
        return (name, reach_idx, ROUND_WEIGHTS.get(name, 0.0))

    return (None, -1, 0.0)
