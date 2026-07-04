from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.domain.value_objects.global_stats import (
    get_comparison,
    get_global_summary,
    get_h2h,
    get_rankings,
    get_top_players,
)
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.session import get_db
from app.schemas.stats import ApiResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=ApiResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Global summary: aggregate totals + ranking leader + best win %."""
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
    """Full ranking with sort, filter, and pagination."""
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
    """Per-category ranking (delegates to get_rankings with category filter)."""
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
    """10 independent top-5 lists by various metrics."""
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
    """Side-by-side comparison of two players."""
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
    """Head-to-head history between two players."""
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
