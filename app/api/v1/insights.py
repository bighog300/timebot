from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.intelligence import InsightsResponse
from app.services.insights_service import insights_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get('/overview', response_model=InsightsResponse)
def insights_overview(lookback_days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    return insights_service.build_dashboard(db=db, lookback_days=lookback_days)


@router.get('/trends')
def insights_trends(lookback_days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    dashboard = insights_service.build_dashboard(db=db, lookback_days=lookback_days)
    return {"lookback_days": lookback_days, "trends": dashboard["volume_trends"]}


@router.get('/rollups')
def insights_rollups(lookback_days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    dashboard = insights_service.build_dashboard(db=db, lookback_days=lookback_days)
    return {
        "lookback_days": lookback_days,
        "action_item_summary": dashboard["action_item_summary"],
        "category_distribution": dashboard["category_distribution"],
        "source_distribution": dashboard["source_distribution"],
        "relationship_summary": dashboard["relationship_summary"],
    }
