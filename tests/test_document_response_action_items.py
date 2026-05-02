from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.document import DocumentResponse


def _base_payload():
    return {
        "id": uuid4(),
        "filename": "doc.pdf",
        "file_type": "pdf",
        "file_size": 100,
        "source": "upload",
        "upload_date": datetime.now(timezone.utc),
        "processing_status": "completed",
    }


def test_document_response_action_items_accepts_string_list():
    payload = _base_payload() | {"action_items": ["Call client", "Send follow up"]}
    response = DocumentResponse.model_validate(payload)
    assert response.action_items == ["Call client", "Send follow up"]


def test_document_response_action_items_uses_action_item_texts_alias():
    payload = _base_payload() | {"action_item_texts": ["File appeal", "Draft response"]}
    response = DocumentResponse.model_validate(payload)
    assert response.action_items == ["File appeal", "Draft response"]


def test_document_response_action_items_filters_non_strings():
    payload = _base_payload() | {"action_items": ["Keep", {"content": "Drop"}, None, "  "]}
    response = DocumentResponse.model_validate(payload)
    assert response.action_items == ["Keep"]
