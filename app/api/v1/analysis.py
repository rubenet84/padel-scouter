"""
Endpoints de análisis IA de jugadores.

Permite ejecutar y recuperar análisis generados por Gemini AI para cada
jugador. Usa el caso de uso AnalyzePlayerUseCase del dominio, con caché
en Redis para evitar llamadas repetidas a la API de IA.

Arquitectura: Capa API — orquesta la capa de dominio (use case) y la capa
de infraestructura (Gemini, Redis). No contiene lógica de análisis propia.
"""
import json
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user

logger = logging.getLogger(__name__)
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import PlayerModel, AnalysisModel, UserModel
from app.infrastructure.ai.gemini_client import analyze_player_with_ai
from app.infrastructure.cache.redis_client import redis_cache
from app.domain.entities.player import Player, PlayerStats
from app.domain.use_cases.analyze_player import AnalyzePlayerUseCase
from app.services.computed_stats_service import get_computed_stats
from app.schemas.player import AnalysisPublicSchema

router = APIRouter(prefix="/analysis", tags=["analysis"])


class GeminiClientWrapper:
    """Adaptador que envuelve la función analyze_player_with_ai para que
    cumpla con la interfaz esperada por AnalyzePlayerUseCase."""
    def analyze_player_with_ai(self, data: dict) -> dict:
        return analyze_player_with_ai(data)


@router.post("/{player_id}", response_model=AnalysisPublicSchema, status_code=201)
def analyze_player(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Ejecuta un análisis completo del jugador usando IA (Gemini).

    Flujo:
    1. Verifica que el jugador pertenezca al usuario (OWASP A01).
    2. Construye la entidad de dominio Player desde el modelo de BD.
    3. Obtiene estadísticas computadas (torneos, win_rate, FEP).
    4. Ejecuta AnalyzePlayerUseCase que calcula power level, consulta
       a Gemini y devuelve el AnalysisResult.
    5. Persiste el análisis en la tabla analyses.
    6. Si Gemini falla, devuelve 503 con mensaje amigable.

    El análisis se cachea en Redis para no gastar cuota de API en
    análisis repetidos del mismo jugador con los mismos stats.
    """
    player_model = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player_model:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Construir entidad de dominio
    stats = PlayerStats(
        derecha=player_model.derecha, reves=player_model.reves,
        volea_derecha=player_model.volea_derecha, volea_reves=player_model.volea_reves,
        bandeja=player_model.bandeja,
        vibora=player_model.vibora, remate=player_model.remate,
        globo=player_model.globo, saque=player_model.saque,
        bajada_pared=player_model.bajada_pared,
        velocidad=player_model.velocidad, resistencia=player_model.resistencia,
        reflejos=player_model.reflejos, tactica=player_model.tactica,
        presion=player_model.presion,
        trabajo_en_pareja=player_model.trabajo_en_pareja,
    )
    player = Player(
        id=player_model.id,
        name=player_model.name,
        category=player_model.category,
        stats=stats,
    )

    # Obtener stats computados desde partidos + torneos reales
    computed_stats = get_computed_stats(db, player_id)

    # Ejecutar caso de uso
    try:
        use_case = AnalyzePlayerUseCase(
            ai_client=GeminiClientWrapper(),
            cache=redis_cache,
        )
        result = use_case.execute(player, computed_stats=computed_stats)
    except Exception as e:
        logger.error("Error ejecutando análisis para player %s: %s", player_id, e)
        raise HTTPException(
            status_code=503,
            detail="El servicio de análisis no está disponible. Intentalo de nuevo en unos minutos.",
        )

    # Persistir análisis
    analysis = AnalysisModel(
        player_id=player.id,
        power_level=result.power_level,
        category=result.category,
        ai_description=result.ai_description,
        strengths=json.dumps(result.strengths),
        weaknesses=json.dumps(result.weaknesses),
        improvement_plan=result.improvement_plan,
        golpe_definitivo=result.golpe_definitivo,
        golpe_descripcion=result.golpe_descripcion,
        golpe_puntuacion=result.golpe_puntuacion,
        nivel_amenaza=result.nivel_amenaza,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return AnalysisPublicSchema(
        id=analysis.id,
        player_id=analysis.player_id,
        power_level=analysis.power_level,
        category=analysis.category,
        ai_description=analysis.ai_description,
        strengths=json.loads(analysis.strengths),
        weaknesses=json.loads(analysis.weaknesses),
        improvement_plan=analysis.improvement_plan,
        golpe_definitivo=analysis.golpe_definitivo,
        golpe_descripcion=analysis.golpe_descripcion,
        golpe_puntuacion=analysis.golpe_puntuacion,
        nivel_amenaza=analysis.nivel_amenaza,
    )


@router.get("/{player_id}", response_model=list[AnalysisPublicSchema])
def get_player_analyses(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Recupera el historial completo de análisis IA de un jugador.

    Ordenados por fecha de creación (más reciente primero).
    Los campos JSON (strengths, weaknesses) se deserializan con manejo
    seguro de errores de formato.
    """
    # OWASP A01: verificar que el player pertenece al usuario actual
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    analyses = db.query(AnalysisModel).filter(
        AnalysisModel.player_id == player_id
    ).all()

    def _safe_json_loads(val: str) -> list:
        """Deserializa JSON de forma segura, devolviendo lista vacía si falla."""
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return []

    return [
        AnalysisPublicSchema(
            id=a.id,
            player_id=a.player_id,
            power_level=a.power_level,
            category=a.category,
            ai_description=a.ai_description,
            strengths=_safe_json_loads(a.strengths),
            weaknesses=_safe_json_loads(a.weaknesses),
            improvement_plan=a.improvement_plan,
            golpe_definitivo=a.golpe_definitivo,
            golpe_descripcion=a.golpe_descripcion,
            golpe_puntuacion=a.golpe_puntuacion,
            nivel_amenaza=a.nivel_amenaza,
        )
        for a in analyses
    ]
