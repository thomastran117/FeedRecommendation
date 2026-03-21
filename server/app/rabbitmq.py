import json
from typing import Any

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from app.config import settings

EVENTS_EXCHANGE = "events"

_connection: AbstractRobustConnection | None = None


async def connect() -> None:
    global _connection
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)


async def disconnect() -> None:
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
    _connection = None


async def publish(routing_key: str, payload: dict[str, Any]) -> None:
    if _connection is None or _connection.is_closed:
        raise RuntimeError("RabbitMQ connection is not open")

    async with _connection.channel() as channel:
        exchange = await channel.declare_exchange(
            EVENTS_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )
