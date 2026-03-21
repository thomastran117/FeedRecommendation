from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app import rabbitmq

router = APIRouter()


class EventType(StrEnum):
    POST_SEARCH = "post.search"
    POST_CLICK = "post.click"


class EventRequest(BaseModel):
    event_type: EventType
    payload: dict[str, Any] = {}


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def publish_event(body: EventRequest):
    message = {
        "event_type": body.event_type,
        "payload": body.payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await rabbitmq.publish(routing_key=body.event_type, payload=message)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to publish event: {exc}",
        )
    return {"status": "accepted", "event_type": body.event_type}
