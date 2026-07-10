from dataclasses import dataclass
from uuid import UUID
import json

from app.domain.entities.player import Player
from app.domain.entities.analysis import AnalysisResult
from app.domain.value_objects.power_level import calculate_power_level
from app.domain.value_objects.category import PlayerCategory
from app.domain.value_objects.computed_stats import ComputedStats
from app.domain.value_objects.golpe_definitivo import (
    find_strongest_stat,
    nivel_amenaza_from_score,
)


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

    def execute(
        self,
        player: Player,
        computed_stats: ComputedStats | None = None,
    ) -> AnalysisResult:
        # 1. Calcular poder de combate y golpe definitivo base
        power_level = calculate_power_level(
            player.stats,
            computed_stats=computed_stats,
        )
        stat_key, stat_label, stat_cat, stat_value = find_strongest_stat(player.stats)
        nivel_amenaza = nivel_amenaza_from_score(stat_value)

        # 2. Preparar datos para IA
        player_data = {
            "name": player.name,
            "category": player.category.value,
            "power_level": power_level,
            "derecha": player.stats.derecha,
            "reves": player.stats.reves,
            "volea_derecha": player.stats.volea_derecha,
            "volea_reves": player.stats.volea_reves,
            "bandeja": player.stats.bandeja,
            "vibora": player.stats.vibora,
            "remate": player.stats.remate,
            "globo": player.stats.globo,
            "saque": player.stats.saque,
            "bajada_pared": player.stats.bajada_pared,
            "velocidad": player.stats.velocidad,
            "resistencia": player.stats.resistencia,
            "reflejos": player.stats.reflejos,
            "tactica": player.stats.tactica,
            "presion": player.stats.presion,
            "trabajo_en_pareja": player.stats.trabajo_en_pareja,
            "golpe_stat_key": stat_key,
            "golpe_stat_label": stat_label,
            "golpe_stat_categoria": stat_cat,
            "golpe_puntuacion": stat_value,
            "nivel_amenaza": nivel_amenaza,
        }

        # 3. Intentar cache primero
        cached = self.cache.get("analysis", player_data)
        if cached:
            ai_result = cached
        else:
            ai_result = self.ai_client.analyze_player_with_ai(player_data)
            self.cache.set("analysis", player_data, ai_result)

        golpe_nombre = (ai_result.get("golpe_definitivo") or f"{stat_label} Definitivo").strip("'\"")
        golpe_descripcion = ai_result.get("descripcion_golpe") or (
            f"Su {stat_label.lower()} alcanza un poder de {stat_value}/100. "
            f"Una técnica {stat_cat} que desata energía pura sobre la pista."
        )

        # 4. Construir resultado
        return AnalysisResult(
            player_id=player.id,
            power_level=power_level,
            category=player.category,
            ai_description=ai_result.get("descripcion_epica", ""),
            strengths=ai_result.get("fortalezas", []),
            weaknesses=ai_result.get("debilidades", []),
            improvement_plan=ai_result.get("plan_mejora", ""),
            golpe_definitivo=golpe_nombre,
            golpe_descripcion=golpe_descripcion,
            golpe_puntuacion=stat_value,
            nivel_amenaza=nivel_amenaza,
        )
