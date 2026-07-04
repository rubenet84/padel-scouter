from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.domain.value_objects.global_stats import get_global_summary
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
