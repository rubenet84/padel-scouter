from dataclasses import dataclass, field
from uuid import UUID, uuid4
from app.domain.value_objects.category import PlayerCategory


@dataclass
class PlayerStats:
    # Técnica (0-100)
    derecha:       int = 50
    reves:         int = 50
    volea_derecha: int = 50
    volea_reves:   int = 50
    bandeja:       int = 50
    vibora:        int = 50
    remate:        int = 50
    globo:         int = 50
    saque:         int = 50
    bajada_pared:  int = 50

    # Físico (0-100)
    velocidad:     int = 50
    resistencia:   int = 50
    reflejos:      int = 50

    # Mental/Táctico (0-100)
    tactica:             int = 50
    presion:             int = 50
    trabajo_en_pareja:   int = 50


@dataclass
class Player:
    name:     str
    category: PlayerCategory
    stats:    PlayerStats
    id:       UUID = field(default_factory=uuid4)