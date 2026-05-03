from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.models.document import Document
from app.models.user import User
from app.services.auth import auth_service
from app.services.notification import manager

router = APIRouter(prefix="/ws", tags=["websocket"])


def _extract_bearer_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return websocket.query_params.get("token")


def _get_ws_db() -> Session:
    return SessionLocal()


def _authenticate_websocket(websocket: WebSocket, db: Session) -> User | None:
    token = _extract_bearer_token(websocket)
    if not token:
        return None
    try:
        payload = auth_service.decode_token(token)
    except Exception:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        return None
    return user


@router.websocket("/documents/{document_id}")
async def ws_document(websocket: WebSocket, document_id: str):
    db = _get_ws_db()
    try:
        user = _authenticate_websocket(websocket, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        document = db.query(Document).filter(Document.id == doc_uuid).first()
        is_admin = (user.role or "viewer").lower() == "admin"
        if not document or (document.user_id != user.id and not is_admin):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        channel = str(document.id)
    finally:
        db.close()
    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)




@router.get("/all")
def ws_all_upgrade_hint():
    return {"detail": "This endpoint is WebSocket-only. Connect via ws(s)://.../api/v1/ws/all"}

@router.websocket("/all")
async def ws_all(websocket: WebSocket):
    db = _get_ws_db()
    try:
        user = _authenticate_websocket(websocket, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        if (user.role or "viewer").lower() != "admin":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        db.close()
    await manager.connect(websocket, "__all__")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "__all__")
