"""
Memory Message Queue Adapter - In-memory implementation for testing.

This adapter stores messages in memory using asyncio queues.
Perfect for unit tests and local development without external services.

Usage:
    queue = MemoryQueueAdapter()
    await queue.connect()
    await queue.publish("validation", Message(event_type="decision.proposed", payload={...}))
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from collections import defaultdict

from core.ports.message_queue import MessageQueueProtocol, Message, MessageHandler

logger = logging.getLogger(__name__)


class MemoryQueueAdapter(MessageQueueProtocol):
    """
    In-memory implementation of MessageQueueProtocol.

    Uses asyncio.Queue for message delivery:
    - Fast and lightweight
    - No external dependencies
    - Messages lost on restart (testing only)
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize in-memory queue.

        Args:
            max_size: Maximum queue size (per queue)
        """
        self.max_size = max_size
        self._queues: Dict[str, asyncio.Queue] = defaultdict(
            lambda: asyncio.Queue(maxsize=max_size)
        )
        self._handlers: Dict[str, List[MessageHandler]] = defaultdict(list)
        self._pending_acks: Dict[str, Message] = {}
        self._connected = False
        self._running = False
        self._consumer_tasks: List[asyncio.Task] = []
        self._message_count: Dict[str, int] = defaultdict(int)
        logger.info("Memory queue adapter initialized")

    async def connect(self) -> None:
        """Mark as connected (no-op for memory)."""
        self._connected = True
        self._running = True
        logger.info("Memory queue connected")

    async def disconnect(self) -> None:
        """Stop all consumers and clear queues."""
        self._running = False
        self._connected = False

        # Cancel consumer tasks
        for task in self._consumer_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._consumer_tasks.clear()
        self._queues.clear()
        self._handlers.clear()
        self._pending_acks.clear()
        logger.info("Memory queue disconnected")

    async def publish(self, queue: str, message: Message) -> None:
        """Publish a message to a queue."""
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")

        try:
            await self._queues[queue].put(message)
            self._message_count[queue] += 1
            logger.debug(f"Published message {message.id} to queue {queue}")

            # If there are handlers, process immediately (for sync testing)
            if self._handlers[queue]:
                for handler in self._handlers[queue]:
                    asyncio.create_task(self._process_message(queue, handler))

        except asyncio.QueueFull:
            logger.error(f"Queue {queue} is full")
            raise

    async def subscribe(
        self,
        queue: str,
        handler: MessageHandler,
        prefetch_count: int = 1
    ) -> None:
        """Subscribe to a queue and process messages."""
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")

        self._handlers[queue].append(handler)
        logger.info(f"Subscribed to queue: {queue}")

        # Start consumer task
        task = asyncio.create_task(self._consume(queue, handler, prefetch_count))
        self._consumer_tasks.append(task)

    async def _consume(
        self,
        queue: str,
        handler: MessageHandler,
        prefetch_count: int
    ) -> None:
        """Consumer loop for a queue."""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._queues[queue].get(),
                    timeout=1.0
                )

                # Store for acknowledgment
                self._pending_acks[message.id] = message

                # Process message
                try:
                    await handler(message)
                    # Auto-acknowledge
                    if message.id in self._pending_acks:
                        await self.acknowledge(message.id)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def _process_message(self, queue: str, handler: MessageHandler) -> None:
        """Process a single message from queue."""
        try:
            message = self._queues[queue].get_nowait()
            self._pending_acks[message.id] = message
            await handler(message)
            if message.id in self._pending_acks:
                await self.acknowledge(message.id)
        except asyncio.QueueEmpty:
            pass
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def acknowledge(self, message_id: str) -> None:
        """Acknowledge successful processing of a message."""
        self._pending_acks.pop(message_id, None)
        logger.debug(f"Acknowledged message: {message_id}")

    async def reject(self, message_id: str, requeue: bool = False) -> None:
        """Reject a message."""
        message = self._pending_acks.pop(message_id, None)
        if message and requeue:
            # Requeue the message
            queue_name = None
            for q, handlers in self._handlers.items():
                if handlers:
                    queue_name = q
                    break
            if queue_name:
                await self._queues[queue_name].put(message)
        logger.debug(f"Rejected message: {message_id}, requeue={requeue}")

    async def health_check(self) -> bool:
        """Check if the queue is healthy."""
        return self._connected

    async def get_queue_stats(self, queue: str) -> Dict[str, Any]:
        """Get statistics for a queue."""
        if not self._connected:
            return {"error": "Not connected"}

        q = self._queues.get(queue)
        return {
            "name": queue,
            "message_count": q.qsize() if q else 0,
            "total_published": self._message_count.get(queue, 0),
            "consumer_count": len(self._handlers.get(queue, [])),
            "pending_acks": len(self._pending_acks),
        }

    # Test helpers

    async def get_pending_messages(self, queue: str) -> List[Message]:
        """Get all pending messages in a queue (for testing)."""
        messages = []
        q = self._queues.get(queue)
        if q:
            while not q.empty():
                try:
                    messages.append(q.get_nowait())
                except asyncio.QueueEmpty:
                    break
        # Put them back
        for msg in messages:
            await q.put(msg)
        return messages

    def clear_queue(self, queue: str) -> None:
        """Clear a queue (for testing)."""
        q = self._queues.get(queue)
        if q:
            while not q.empty():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    break
