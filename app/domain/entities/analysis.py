from dataclasses import dataclass
from uuid import UUID
from app.domain.value_objects.category import PlayerCategory


@dataclass
class AnalysisResult:
    player_id:        UUID
    power_level:      int          # 0 - 9999
    category:         PlayerCategory
    ai_description:   str          # Narrativa generada por Gemini
    strengths:        list[str]
    weaknesses:       list[str]
    improvement_plan: str
    golpe_definitivo: str = "Por determinar"
    golpe_descripcion: str = ""
    golpe_puntuacion:  int = 0
    nivel_amenaza:    str = "MEDIO"