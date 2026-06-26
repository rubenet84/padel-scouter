from dataclasses import dataclass
from uuid import UUID
import json

from app.domain.entities.player import Player
from app.domain.entities.analysis import AnalysisResult
from app.domain.value_objects.power_level import calculate_power_level
from app.domain.value_objects.category import PlayerCategory


@dataclass
class AnalyzePlayerUseCase:
    """
    Orquesta el análisis completo de un jugador:
    1. Calcula poder de combate
    2. Llama a la IA (con cache)
    3. Devuelve AnalysisResult
    """
    ai_client: object    # gemini_client o mock en tests
    cache: object        # redis_cache o mock en tests

    def execute(self, player: Player) -> AnalysisResult:
        # 1. Calcular poder de combate
        power_level = calculate_power_level(player.stats, player.category)

        # 2. Preparar datos para IA
        player_data = {
            "name": player.name,
            "category": player.category.value,
            "power_level": power_level,
            "derecha": player.stats.derecha,
            "reves": player.stats.reves,
            "volea": player.stats.volea,
            "bandeja": player.stats.bandeja,
            "vibora": player.stats.vibora,
            "smash": player.stats.smash,
            "lob": player.stats.lob,
            "saque": player.stats.saque,
            "bajada_pared": player.stats.bajada_pared,
            "velocidad": player.stats.velocidad,
            "resistencia": player.stats.resistencia,
            "reflejos": player.stats.reflejos,
            "tactica": player.stats.tactica,
            "presion": player.stats.presion,
            "trabajo_en_pareja": player.stats.trabajo_en_pareja,
            "torneos_jugados": player.stats.torneos_jugados,
            "victorias": player.stats.victorias,
            "puntos_ranking_fep": player.stats.puntos_ranking_fep,
        }

        # 3. Intentar cache primero
        cached = self.cache.get("analysis", player_data)
        if cached:
            ai_result = cached
        else:
            ai_result = self.ai_client.analyze_player_with_ai(player_data)
            self.cache.set("analysis", player_data, ai_result)

        # 4. Construir resultado
        return AnalysisResult(
            player_id=player.id,
            power_level=power_level,
            category=player.category,
            ai_description=ai_result.get("descripcion_epica", ""),
            strengths=ai_result.get("fortalezas", []),
            weaknesses=ai_result.get("debilidades", []),
            improvement_plan=ai_result.get("plan_mejora", ""),
            golpe_definitivo=ai_result.get("golpe_definitivo", "Por determinar"),
            nivel_amenaza=ai_result.get("nivel_amenaza", "MEDIO"),
        )