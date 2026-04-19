from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.notification import manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/documents/{document_id}")
async def ws_document(websocket: WebSocket, document_id: str):
    await manager.connect(websocket, document_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)


@router.websocket("/all")
async def ws_all(websocket: WebSocket):
    await manager.connect(websocket, "__all__")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "__all__")
