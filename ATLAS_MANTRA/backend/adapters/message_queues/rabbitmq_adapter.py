"""
RabbitMQ Message Queue Adapter - Implementation using RabbitMQ.

RabbitMQ provides reliable message delivery with:
- Durable queues and messages
- Message acknowledgment
- Dead letter exchanges
- Consumer prefetch

Requirements:
    pip install aio-pika

Usage:
    queue = RabbitMQAdapter(url="amqp://guest:guest@localhost:5672/")
    await queue.connect()
    await queue.publish("validation", Message(event_type="decision.proposed", payload={...}))
"""

import json
import logging
from typing import Dict, Any, Optional

import aio_pika
from aio_pika import Message as AioPikaMessage, DeliveryMode

from core.ports.message_queue import MessageQueueProtocol, Message, MessageHandler

logger = logging.getLogger(__name__)


class RabbitMQAdapter(MessageQueueProtocol):
    """
    RabbitMQ implementation of MessageQueueProtocol.

    Provides reliable message delivery with:
    - Durable queues (survive restarts)
    - Persistent messages
    - Dead letter handling
    - Consumer acknowledgment
    """

    def __init__(
        self,
        url: str = "amqp://guest:guest@localhost:5672/",
        exchange_name: str = "mantra_events",
        prefetch_count: int = 10,
    ):
        """
        Initialize RabbitMQ adapter.

        Args:
            url: AMQP connection URL
            exchange_name: Exchange name for routing
            prefetch_count: Default prefetch count
        """
        self.url = url
        self.exchange_name = exchange_name
        self.default_prefetch = prefetch_count
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._pending_acks: Dict[str, aio_pika.IncomingMessage] = {}
        logger.info(f"RabbitMQ adapter initialized: exchange={exchange_name}")

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(self.url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.default_prefetch)

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            logger.info(f"Connected to RabbitMQ: {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ."""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")

    async def publish(self, queue: str, message: Message) -> None:
        """Publish a message to a queue."""
        if not self.exchange:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")

        try:
            body = json.dumps(message.to_dict()).encode()
            amqp_message = AioPikaMessage(
                body=body,
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=message.id,
                correlation_id=message.correlation_id,
                content_type="application/json",
            )

            # Use queue name as routing key
            await self.exchange.publish(amqp_message, routing_key=queue)
            logger.debug(f"Published message {message.id} to queue {queue}")
        except Exception as e:
            logger.error(f"Failed to publish message to {queue}: {e}")
            raise

    async def subscribe(
        self,
        queue: str,
        handler: MessageHandler,
        prefetch_count: int = 1
    ) -> None:
        """Subscribe to a queue and process messages."""
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")

        try:
            # Set prefetch for this consumer
            await self.channel.set_qos(prefetch_count=prefetch_count)

            # Declare queue
            queue_obj = await self.channel.declare_queue(
                queue,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": f"{self.exchange_name}.dlx",
                    "x-dead-letter-routing-key": f"{queue}.dead",
                }
            )

            # Bind queue to exchange
            await queue_obj.bind(self.exchange, routing_key=queue)

            # Set up consumer
            async def on_message(amqp_message: aio_pika.IncomingMessage):
                try:
                    data = json.loads(amqp_message.body.decode())
                    message = Message.from_dict(data)

                    # Store for acknowledgment
                    self._pending_acks[message.id] = amqp_message

                    # Process message
                    await handler(message)

                    # Auto-acknowledge if still pending
                    if message.id in self._pending_acks:
                        await self.acknowledge(message.id)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Reject and don't requeue (send to DLQ)
                    await amqp_message.reject(requeue=False)

            await queue_obj.consume(on_message)
            logger.info(f"Subscribed to queue: {queue}")

        except Exception as e:
            logger.error(f"Failed to subscribe to {queue}: {e}")
            raise

    async def acknowledge(self, message_id: str) -> None:
        """Acknowledge successful processing of a message."""
        amqp_message = self._pending_acks.pop(message_id, None)
        if amqp_message:
            await amqp_message.ack()
            logger.debug(f"Acknowledged message: {message_id}")

    async def reject(self, message_id: str, requeue: bool = False) -> None:
        """Reject a message."""
        amqp_message = self._pending_acks.pop(message_id, None)
        if amqp_message:
            await amqp_message.reject(requeue=requeue)
            logger.debug(f"Rejected message: {message_id}, requeue={requeue}")

    async def health_check(self) -> bool:
        """Check if RabbitMQ is healthy."""
        try:
            if not self.connection or self.connection.is_closed:
                return False
            if not self.channel or self.channel.is_closed:
                return False
            return True
        except Exception:
            return False

    async def get_queue_stats(self, queue: str) -> Dict[str, Any]:
        """Get statistics for a queue."""
        if not self.channel:
            return {"error": "Not connected"}

        try:
            queue_obj = await self.channel.declare_queue(
                queue,
                durable=True,
                passive=True,  # Don't create if not exists
            )
            return {
                "name": queue,
                "message_count": queue_obj.declaration_result.message_count,
                "consumer_count": queue_obj.declaration_result.consumer_count,
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats for {queue}: {e}")
            return {"error": str(e)}
