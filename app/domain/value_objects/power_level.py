from app.domain.entities.player import PlayerStats
from app.domain.value_objects.category import PlayerCategory


def calculate_power_level(stats: PlayerStats, category: PlayerCategory) -> int:
    """
    Calcula el poder de combate padelístico (0 - 9999).

    Rangos por categoría:
      Iniciación  →  100 - 1499
      5ª          → 1500 - 2999
      4ª          → 3000 - 4499
      3ª          → 4500 - 5999
      2ª          → 6000 - 7499
      1ª          → 7500 - 8999
      PRO         → 9000 - 9999
    """
    tecnica = (
        stats.derecha      * 0.12 +
        stats.reves        * 0.10 +
        stats.volea        * 0.10 +
        stats.bandeja      * 0.10 +
        stats.vibora       * 0.08 +
        stats.smash        * 0.08 +
        stats.lob          * 0.06 +
        stats.saque        * 0.08 +
        stats.bajada_pared * 0.08
    )  # suma pesos: 0.80 → escala sobre 100

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

    win_rate         = stats.victorias / max(stats.torneos_jugados, 1)
    competitive      = (
        (stats.puntos_ranking_fep / 10) +
        (win_rate * 300) +
        (category.weight() * 100)
    )

    raw_score = (
        tecnica   * 0.45 +
        fisico    * 0.25 +
        mental    * 0.20 +
        competitive * 0.10
    )

    # Anclar al rango de la categoría declarada
    ranges = {
        PlayerCategory.INICIACION: (100,  1499),
        PlayerCategory.QUINTA:     (1500, 2999),
        PlayerCategory.CUARTA:     (3000, 4499),
        PlayerCategory.TERCERA:    (4500, 5999),
        PlayerCategory.SEGUNDA:    (6000, 7499),
        PlayerCategory.PRIMERA:    (7500, 8999),
        PlayerCategory.PRO:        (9000, 9999),
    }
    low, high = ranges[category]
    anchored = low + int((raw_score / 100) * (high - low))
    return max(low, min(anchored, high))


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