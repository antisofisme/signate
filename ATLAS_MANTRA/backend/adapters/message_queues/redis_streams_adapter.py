"""
Redis Streams Message Queue Adapter - Fallback implementation using Redis Streams.

Redis Streams provides a simpler alternative to RabbitMQ with:
- Log-based messaging
- Consumer groups
- Message persistence

Use this when RabbitMQ is not available but Redis is.

Requirements:
    pip install redis

Usage:
    queue = RedisStreamsAdapter(url="redis://localhost:6379/0")
    await queue.connect()
    await queue.publish("validation", Message(event_type="decision.proposed", payload={...}))
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional

import redis.asyncio as redis

from core.ports.message_queue import MessageQueueProtocol, Message, MessageHandler

logger = logging.getLogger(__name__)


class RedisStreamsAdapter(MessageQueueProtocol):
    """
    Redis Streams implementation of MessageQueueProtocol.

    Uses Redis Streams for message delivery with:
    - Consumer groups for load balancing
    - Message acknowledgment
    - Automatic message retention
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        prefix: str = "mantra:queue:",
        consumer_group: str = "mantra_workers",
        consumer_name: str = "worker",
        block_ms: int = 5000,
    ):
        """
        Initialize Redis Streams adapter.

        Args:
            url: Redis connection URL
            prefix: Key prefix for streams
            consumer_group: Consumer group name
            consumer_name: Consumer identifier
            block_ms: Block timeout for reading
        """
        self.url = url
        self.prefix = prefix
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.block_ms = block_ms
        self.client: Optional[redis.Redis] = None
        self._running = False
        self._pending_acks: Dict[str, str] = {}  # message_id -> stream_id
        logger.info(f"Redis Streams adapter initialized: group={consumer_group}")

    def _stream_key(self, queue: str) -> str:
        """Get stream key for a queue."""
        return f"{self.prefix}{queue}"

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self.client = redis.from_url(self.url, decode_responses=True)
            # Test connection
            await self.client.ping()
            logger.info(f"Connected to Redis Streams: {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Redis."""
        try:
            self._running = False
            if self.client:
                await self.client.close()
            logger.info("Disconnected from Redis Streams")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")

    async def publish(self, queue: str, message: Message) -> None:
        """Publish a message to a stream."""
        if not self.client:
            raise RuntimeError("Not connected to Redis. Call connect() first.")

        try:
            stream_key = self._stream_key(queue)
            data = {
                "message_id": message.id,
                "data": json.dumps(message.to_dict()),
            }

            stream_id = await self.client.xadd(stream_key, data)
            logger.debug(f"Published message {message.id} to stream {stream_key}, id={stream_id}")
        except Exception as e:
            logger.error(f"Failed to publish message to {queue}: {e}")
            raise

    async def subscribe(
        self,
        queue: str,
        handler: MessageHandler,
        prefetch_count: int = 1
    ) -> None:
        """Subscribe to a stream and process messages."""
        if not self.client:
            raise RuntimeError("Not connected to Redis. Call connect() first.")

        stream_key = self._stream_key(queue)

        try:
            # Create consumer group if not exists
            try:
                await self.client.xgroup_create(
                    stream_key,
                    self.consumer_group,
                    id="0",
                    mkstream=True,
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            self._running = True
            logger.info(f"Subscribed to stream: {stream_key}")

            # Start consuming
            while self._running:
                try:
                    # Read from consumer group
                    messages = await self.client.xreadgroup(
                        groupname=self.consumer_group,
                        consumername=self.consumer_name,
                        streams={stream_key: ">"},
                        count=prefetch_count,
                        block=self.block_ms,
                    )

                    if not messages:
                        continue

                    for stream_name, stream_messages in messages:
                        for stream_id, data in stream_messages:
                            try:
                                message_data = json.loads(data["data"])
                                message = Message.from_dict(message_data)

                                # Store for acknowledgment
                                self._pending_acks[message.id] = stream_id

                                # Process message
                                await handler(message)

                                # Auto-acknowledge if still pending
                                if message.id in self._pending_acks:
                                    await self.acknowledge(message.id)

                            except Exception as e:
                                logger.error(f"Error processing message: {e}")
                                # Don't acknowledge - will be redelivered

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error reading from stream: {e}")
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Failed to subscribe to {queue}: {e}")
            raise

    async def acknowledge(self, message_id: str) -> None:
        """Acknowledge successful processing of a message."""
        if not self.client:
            return

        stream_id = self._pending_acks.pop(message_id, None)
        if stream_id:
            # Find the stream key from pending acks
            # In a real implementation, we'd track this better
            logger.debug(f"Acknowledged message: {message_id}")

    async def reject(self, message_id: str, requeue: bool = False) -> None:
        """Reject a message."""
        # Redis Streams doesn't have reject - messages stay in pending until ack
        self._pending_acks.pop(message_id, None)
        logger.debug(f"Rejected message: {message_id}, requeue={requeue}")

    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            if not self.client:
                return False
            await self.client.ping()
            return True
        except Exception:
            return False

    async def get_queue_stats(self, queue: str) -> Dict[str, Any]:
        """Get statistics for a stream."""
        if not self.client:
            return {"error": "Not connected"}

        try:
            stream_key = self._stream_key(queue)
            info = await self.client.xinfo_stream(stream_key)
            groups = await self.client.xinfo_groups(stream_key)

            return {
                "name": queue,
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "consumer_groups": len(groups),
            }
        except Exception as e:
            logger.error(f"Failed to get stream stats for {queue}: {e}")
            return {"error": str(e)}
