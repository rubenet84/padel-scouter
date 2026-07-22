"""
Endpoints de estadísticas globales: ranking, top jugadores, comparador,
H2H, récords comunitarios, categorías, evolución y highlights.

Todos los endpoints delegan la lógica de cálculo a los servicios en
app/services/. Esta capa solo se encarga de:
- Validar parámetros de entrada (UUIDs, formatos de fecha).
- Verificar autenticación (JWT requerido en todos los endpoints).
- Formatear la respuesta usando ApiResponse.

Arquitectura: Capa API — orquestación pura, sin lógica de negocio.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.services.category_service import get_category_details
from app.services.comparison_service import get_comparison, get_h2h
from app.services.highlights_service import get_community_highlights, get_evolution, get_records
from app.services.ranking_service import get_rankings, get_top_players
from app.services.summary_service import get_global_summary
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.session import get_db
from app.schemas.stats import ApiResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=ApiResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Resumen global: totales agregados + líder de ranking + mejor % victorias."""
    data = get_global_summary(db, current_user.id)
    return ApiResponse(success=True, data=data.model_dump())


@router.get("/ranking", response_model=ApiResponse)
def get_ranking(
    sort_by: str = Query("points", description="Sort column"),
    order: str = Query("desc", description="Sort direction: asc or desc"),
    category: str | None = Query(None, description="Filter by category name"),
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Ranking completo con ordenación, filtros y paginación."""
    filters = {
        "category": category,
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    data = get_rankings(
        db,
        current_user.id,
        sort_by=sort_by,
        order=order,
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(success=True, data=data.model_dump())


@router.get("/ranking/{category}", response_model=ApiResponse)
def get_ranking_by_category(
    category: str,
    sort_by: str = Query("points", description="Sort column"),
    order: str = Query("desc", description="Sort direction: asc or desc"),
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Ranking filtrado por categoría (delega en get_rankings con filtro)."""
    filters = {
        "category": category,
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    data = get_rankings(
        db,
        current_user.id,
        sort_by=sort_by,
        order=order,
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(success=True, data=data.model_dump())


# ── PR #3: Top Jugadores ─────────────────────────────────────────


@router.get("/top", response_model=ApiResponse)
def get_top(
    category: str | None = Query(None, description="Filter by category name"),
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """10 listas independientes de top 5 jugadores por distintas métricas."""
    filters = {
        "category": category,
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    data = get_top_players(db, current_user.id, filters=filters)
    return ApiResponse(success=True, data=data.model_dump())


# ── PR #3: Comparador ────────────────────────────────────────────


@router.get("/compare/{player_id1}/{player_id2}", response_model=ApiResponse)
def get_compare(
    player_id1: str,
    player_id2: str,
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Comparación lado a lado de dos jugadores con posición en el ranking de su categoría."""
    from uuid import UUID

    try:
        pid1 = UUID(player_id1)
        pid2 = UUID(player_id2)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid player ID format")

    filters = {
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    try:
        data = get_comparison(db, current_user.id, pid1, pid2, filters=filters)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(success=True, data=data.model_dump())


# ── PR #3: H2H ────────────────────────────────────────────────────


@router.get("/h2h/{player_id1}/{player_id2}", response_model=ApiResponse)
def get_h2h_endpoint(
    player_id1: str,
    player_id2: str,
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Historial de enfrentamientos directos (head-to-head) entre dos jugadores."""
    from uuid import UUID

    try:
        pid1 = UUID(player_id1)
        pid2 = UUID(player_id2)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid player ID format")

    filters = {
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    try:
        data = get_h2h(db, current_user.id, pid1, pid2, filters=filters)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(success=True, data=data.model_dump())


# ── PR #4: Community Records ─────────────────────────────────────


@router.get("/records", response_model=ApiResponse)
def get_records_endpoint(
    category: str | None = Query(None, description="Filter by category name"),
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Récords comunitarios: el mejor jugador para cada métrica."""
    filters = {
        "category": category,
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    data = get_records(db, current_user.id, filters=filters)
    return ApiResponse(success=True, data=[r.model_dump() for r in data])


# ── PR #4: Category Stats ────────────────────────────────────────


@router.get("/categories", response_model=ApiResponse)
def get_categories(
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    player_limit: int = Query(5, ge=0, le=20, description="Top N per category"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Todas las categorías con estadísticas agregadas y top N jugadores."""
    filters = {
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    data = get_category_details(
        db, current_user.id, category=None, player_limit=player_limit, filters=filters
    )
    return ApiResponse(success=True, data=[c.model_dump() for c in data])


@router.get("/categories/{category}", response_model=ApiResponse)
def get_category_detail(
    category: str,
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    player_limit: int = Query(5, ge=0, le=20, description="Top N players"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Estadísticas agregadas de una categoría específica."""
    filters = {
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    data = get_category_details(
        db, current_user.id, category=category, player_limit=player_limit, filters=filters
    )
    if not data:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    return ApiResponse(success=True, data=data[0].model_dump())


# ── PR #4: Evolution ─────────────────────────────────────────────


@router.get("/evolution", response_model=ApiResponse)
def get_evolution_endpoint(
    category: str | None = Query(None, description="Filter by category name"),
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Evolución de puntos FEP por jugador con array sparkline (vacío por ahora)."""
    filters = {
        "category": category,
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    data = get_evolution(db, current_user.id, filters=filters)
    return ApiResponse(success=True, data=[e.model_dump() for e in data])


# ── PR #4: Community Highlights ──────────────────────────────────


@router.get("/community", response_model=ApiResponse)
def get_community_endpoint(
    season: int | None = Query(None, description="Filter by year"),
    competition_type: str | None = Query(
        None, description="Filter by type: torneo or amistoso"
    ),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Highlights comunitarios: más puntos, mejor forma, mejor pareja, más activo."""
    filters = {
        "season": season,
        "competition_type": competition_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    data = get_community_highlights(db, current_user.id, filters=filters)
    return ApiResponse(success=True, data=data.model_dump())
