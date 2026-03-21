"""
Standalone consumer — run with:
    python -m app.consumers.events
"""
import asyncio
import json
import logging

import aio_pika

from app.config import settings
from app.rabbitmq import EVENTS_EXCHANGE

logger = logging.getLogger(__name__)

QUEUE_NAME = "events.processor"
BINDING_KEYS = ["post.search", "post.click"]


async def handle_post_search(payload: dict) -> None:
    logger.info("POST SEARCH | query=%s user=%s", payload.get("query"), payload.get("user_id"))


async def handle_post_click(payload: dict) -> None:
    logger.info("POST CLICK  | post_id=%s user=%s", payload.get("post_id"), payload.get("user_id"))


_HANDLERS = {
    "post.search": handle_post_search,
    "post.click": handle_post_click,
}


async def on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=True):
        try:
            data = json.loads(message.body)
        except json.JSONDecodeError:
            logger.warning("Dropping undecodable message: %r", message.body)
            return

        event_type = data.get("event_type")
        handler = _HANDLERS.get(event_type)

        if handler is None:
            logger.warning("No handler for event_type=%r", event_type)
            return

        await handler(data.get("payload", {}))


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("Connecting to RabbitMQ …")

    connection = await aio_pika.connect_robust(settings.rabbitmq_url)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            EVENTS_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        for key in BINDING_KEYS:
            await queue.bind(exchange, routing_key=key)

        logger.info("Waiting for events (queue=%s) …", QUEUE_NAME)
        await queue.consume(on_message)
        await asyncio.get_event_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
