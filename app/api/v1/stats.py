from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.domain.value_objects.global_stats import get_global_summary, get_rankings
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
