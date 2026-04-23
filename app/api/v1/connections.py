from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.relationships import Connection, SyncLog
from app.models.user import User
from app.schemas.connections import (
    ConnectionResponse,
    OAuthStartResponse,
    SyncLogResponse,
    SyncRunResponse,
)
from app.services.connectors.service import connector_service
from app.services.notification import manager

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get('/', response_model=list[ConnectionResponse])
def list_connections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return connector_service.list_connections(db, current_user)


@router.post('/{provider_type}/connect/start', response_model=OAuthStartResponse)
def start_connect(provider_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return connector_service.start_oauth(db, provider_type, current_user)
    except KeyError:
        raise HTTPException(status_code=404, detail='Unsupported provider')
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get('/{provider_type}/connect/callback', response_model=ConnectionResponse)
async def connect_callback(
    provider_type: str,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        conn = connector_service.handle_callback(db, provider_type, code=code, state=state, user=current_user)
    except KeyError:
        raise HTTPException(status_code=404, detail='Unsupported provider')
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'OAuth callback failed: {exc}')

    await manager.send('__all__', {
        'type': 'connection_update',
        'event_version': '1.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'connection_id': str(conn.id),
        'provider_type': conn.type,
        'status': conn.status,
    })
    return conn


@router.post('/{provider_type}/disconnect', response_model=ConnectionResponse)
async def disconnect_provider(provider_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        conn = connector_service.disconnect(db, provider_type, current_user)
    except KeyError:
        raise HTTPException(status_code=404, detail='Unsupported provider')

    await manager.send('__all__', {
        'type': 'connection_update',
        'event_version': '1.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'connection_id': str(conn.id),
        'provider_type': conn.type,
        'status': conn.status,
    })
    return conn


# NOTE (Sprint 4): This endpoint simulates a sync operation.
# Real OAuth-based sync (Google Drive etc.) is implemented in Sprint 4
# of CODEX_PLAN.md. Until then, the status briefly sets to 'syncing' via
# WebSocket but the DB record is immediately marked 'connected' to avoid
# the UI showing a stuck syncing state. Do not remove the two-step status
# writes without implementing real async sync progress tracking.
@router.post('/{provider_type}/sync', response_model=SyncRunResponse)
async def sync_provider(provider_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        conn, _log, result = connector_service.sync_connection(db, provider_type, current_user)
    except KeyError:
        raise HTTPException(status_code=404, detail='Unsupported provider')
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await manager.send('__all__', {
        'type': 'connection_sync',
        'event_version': '1.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'connection_id': str(conn.id),
        'provider_type': conn.type,
        'status': conn.status,
        'sync_progress': conn.sync_progress,
        'last_sync_status': conn.last_sync_status,
    })

    return {
        'message': f'Sync completed for {provider_type}',
        'files_seen': result.files_seen,
        'documents_added': result.added,
        'documents_updated': result.updated,
        'documents_failed': result.failed,
        'bytes_synced': result.bytes_synced,
        'connection': conn,
    }


@router.get('/{provider_type}/sync-logs', response_model=list[SyncLogResponse])
def sync_logs(provider_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conn = db.query(Connection).filter(Connection.type == provider_type, Connection.user_id == current_user.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail='Connection not found')

    return (
        db.query(SyncLog)
        .filter(SyncLog.connection_id == conn.id)
        .order_by(SyncLog.start_time.desc())
        .limit(50)
        .all()
    )
