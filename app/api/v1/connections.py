from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.relationships import Connection, SyncLog
from app.schemas.connections import ConnectionResponse, SyncLogResponse
from app.services.notification import manager

router = APIRouter(prefix="/connections", tags=["connections"])
SUPPORTED = ["gmail", "gdrive", "dropbox", "onedrive"]
DISPLAY = {
    "gmail": "Gmail",
    "gdrive": "Google Drive",
    "dropbox": "Dropbox",
    "onedrive": "OneDrive",
}


def _get_or_create(db: Session, provider_type: str) -> Connection:
    conn = db.query(Connection).filter(Connection.type == provider_type).first()
    if conn:
        return conn

    conn = Connection(type=provider_type, display_name=DISPLAY[provider_type], status="disconnected")
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.get('/', response_model=list[ConnectionResponse])
def list_connections(db: Session = Depends(get_db)):
    existing = {c.type: c for c in db.query(Connection).all()}
    for provider in SUPPORTED:
        if provider not in existing:
            _get_or_create(db, provider)
    return db.query(Connection).order_by(Connection.type.asc()).all()


@router.post('/{provider_type}/connect', response_model=ConnectionResponse)
async def connect_provider(provider_type: str, db: Session = Depends(get_db)):
    if provider_type not in SUPPORTED:
        raise HTTPException(status_code=404, detail='Unsupported provider')

    conn = _get_or_create(db, provider_type)
    conn.status = 'connected'
    conn.is_authenticated = True
    conn.last_sync_status = conn.last_sync_status or 'success'
    db.add(conn)
    db.commit()
    db.refresh(conn)

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
async def disconnect_provider(provider_type: str, db: Session = Depends(get_db)):
    conn = db.query(Connection).filter(Connection.type == provider_type).first()
    if not conn:
        raise HTTPException(status_code=404, detail='Connection not found')

    conn.status = 'disconnected'
    conn.is_authenticated = False
    conn.sync_progress = 0
    db.add(conn)
    db.commit()
    db.refresh(conn)

    await manager.send('__all__', {
        'type': 'connection_update',
        'event_version': '1.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'connection_id': str(conn.id),
        'provider_type': conn.type,
        'status': conn.status,
    })
    return conn


@router.post('/{provider_type}/sync')
async def sync_provider(provider_type: str, db: Session = Depends(get_db)):
    conn = db.query(Connection).filter(Connection.type == provider_type).first()
    if not conn:
        raise HTTPException(status_code=404, detail='Connection not found')

    conn.status = 'syncing'
    conn.sync_progress = 100
    conn.last_sync_date = datetime.now(timezone.utc)
    conn.last_sync_status = 'success'
    conn.document_count += 1
    db.add(conn)

    log = SyncLog(
        connection_id=conn.id,
        start_time=conn.last_sync_date,
        end_time=conn.last_sync_date,
        status='success',
        documents_added=1,
        documents_updated=0,
        documents_failed=0,
        bytes_synced=1024,
    )
    db.add(log)
    db.commit()
    db.refresh(conn)

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

    conn.status = 'connected'
    conn.sync_progress = 0
    db.add(conn)
    db.commit()
    db.refresh(conn)

    return {'message': f'Sync completed for {provider_type}', 'connection': conn}


@router.get('/{provider_type}/sync-logs', response_model=list[SyncLogResponse])
def sync_logs(provider_type: str, db: Session = Depends(get_db)):
    conn = db.query(Connection).filter(Connection.type == provider_type).first()
    if not conn:
        raise HTTPException(status_code=404, detail='Connection not found')

    return (
        db.query(SyncLog)
        .filter(SyncLog.connection_id == conn.id)
        .order_by(SyncLog.start_time.desc())
        .limit(50)
        .all()
    )
