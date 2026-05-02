from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.intelligence import InsightsResponse, StructuredInsightsResponse
from app.models.user import User
from app.services.insights_service import insights_service
from app.services.limit_enforcement import enforce_feature
from app.services.cost_protection import configured_rate_limit, enforce_rate_limit
from app.services.usage import record_usage

router = APIRouter(prefix="/insights", tags=["insights"], dependencies=[Depends(get_current_user)])


@router.get('/overview', response_model=InsightsResponse)
def insights_overview(lookback_days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    enforce_feature(db, current_user.id, "insights_enabled")
    result = insights_service.build_dashboard(db=db, lookback_days=lookback_days)
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    return result


@router.get('/trends')
def insights_trends(lookback_days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    enforce_feature(db, current_user.id, "insights_enabled")
    dashboard = insights_service.build_dashboard(db=db, lookback_days=lookback_days)
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    return {"lookback_days": lookback_days, "trends": dashboard["volume_trends"]}


@router.get('/rollups')
def insights_rollups(lookback_days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    enforce_feature(db, current_user.id, "insights_enabled")
    dashboard = insights_service.build_dashboard(db=db, lookback_days=lookback_days)
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    return {
        "lookback_days": lookback_days,
        "action_item_summary": dashboard["action_item_summary"],
        "category_distribution": dashboard["category_distribution"],
        "source_distribution": dashboard["source_distribution"],
        "relationship_summary": dashboard["relationship_summary"],
    }


@router.get('/structured', response_model=StructuredInsightsResponse)
def structured_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    enforce_feature(db, current_user.id, "insights_enabled")
    result = insights_service.build_structured_insights(db=db, user_id=current_user.id)
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    return result
