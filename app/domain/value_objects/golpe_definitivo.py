from app.domain.entities.player import PlayerStats

# Estadísticas evaluadas para el golpe definitivo (excluye historial competitivo)
SCOUTER_STATS: list[tuple[str, str, str]] = [
    ("derecha", "Derecha", "técnica"),
    ("reves", "Revés", "técnica"),
    ("volea", "Volea", "técnica"),
    ("bandeja", "Bandeja", "técnica"),
    ("vibora", "Víbora", "técnica"),
    ("smash", "Smash", "técnica"),
    ("lob", "Lob", "técnica"),
    ("saque", "Saque", "técnica"),
    ("bajada_pared", "Bajada de pared", "técnica"),
    ("velocidad", "Velocidad", "físico"),
    ("resistencia", "Resistencia", "físico"),
    ("reflejos", "Reflejos", "físico"),
    ("tactica", "Táctica", "mental"),
    ("presion", "Presión", "mental"),
    ("trabajo_en_pareja", "Trabajo en pareja", "mental"),
]


def find_strongest_stat(stats: PlayerStats) -> tuple[str, str, str, int]:
    """Devuelve (clave, etiqueta, categoría, puntuación) del stat más alto."""
    best_key, best_label, best_cat = SCOUTER_STATS[0]
    best_value = getattr(stats, best_key)

    for key, label, cat in SCOUTER_STATS[1:]:
        value = getattr(stats, key)
        if value > best_value:
            best_key, best_label, best_cat, best_value = key, label, cat, value

    return best_key, best_label, best_cat, best_value


def nivel_amenaza_from_score(score: int) -> str:
    if score >= 90:
        return "MUY ALTO"
    if score >= 70:
        return "ALTO"
    if score >= 50:
        return "MEDIO"
    return "BAJO"


def dragon_balls_for_level(nivel: str) -> int:
    return {
        "BAJO": 1,
        "MEDIO": 3,
        "ALTO": 5,
        "MUY ALTO": 7,
    }.get(nivel, 1)
