from app.domain.entities.player import PlayerStats
from app.domain.value_objects.category import PlayerCategory
from app.domain.value_objects.computed_stats import ComputedStats


def calculate_power_level(
    stats: PlayerStats,
    computed_stats: ComputedStats | None = None,
) -> int:
    """
    Calcula el poder de combate padelístico (0 - 9999).

    Solo usa stats reales del jugador (técnica + físico + mental) y
    datos de partidos (competitivo). La categoría NO influye en el
    cálculo — la categoría sugerida se deriva del power level vía
    `classify_by_power()`.

    Cuando `computed_stats` se proporciona, el componente competitivo
    se calcula desde datos reales de partidos.
    """
    tecnica = (
        stats.derecha      * 0.12 +
        stats.reves        * 0.10 +
        ((stats.volea_derecha + stats.volea_reves) / 2) * 0.10 +
        stats.bandeja      * 0.10 +
        stats.vibora       * 0.08 +
        stats.remate       * 0.08 +
        stats.globo         * 0.06 +
        stats.saque        * 0.08 +
        stats.bajada_pared * 0.08
    ) / 0.80  # escalar a 0-100 (pesos suman 80%)

    fisico = (
        stats.velocidad   * 0.35 +
        stats.resistencia * 0.35 +
        stats.reflejos    * 0.30
    )

    mental = (
        stats.tactica           * 0.40 +
        stats.presion           * 0.30 +
        stats.trabajo_en_pareja * 0.30
    )

    if computed_stats:
        win_rate = computed_stats.win_rate / 100
        fep_pts = computed_stats.fep_points
    else:
        win_rate = 0.0
        fep_pts = 0

    competitive = (fep_pts / 10) + (win_rate * 15)

    raw_score = (
        tecnica   * 0.45 +
        fisico    * 0.25 +
        mental    * 0.20 +
        competitive * 0.10
    )

    # Mapeo directo 0-9999, sin anclaje por categoría
    return min(int(raw_score * 100), 9999)


def classify_by_power(power_level: int) -> PlayerCategory:
    """Clasifica un jugador por su poder de combate."""
    if power_level < 1500:
        return PlayerCategory.INICIACION
    elif power_level < 3000:
        return PlayerCategory.QUINTA
    elif power_level < 4500:
        return PlayerCategory.CUARTA
    elif power_level < 6000:
        return PlayerCategory.TERCERA
    elif power_level < 7500:
        return PlayerCategory.SEGUNDA
    elif power_level < 9000:
        return PlayerCategory.PRIMERA
    return PlayerCategory.PRO
