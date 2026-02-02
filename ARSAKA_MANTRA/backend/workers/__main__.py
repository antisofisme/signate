"""
Worker Entry Point - Run MANTRA background workers.

Usage:
    # Run all workers
    python -m workers

    # Run specific worker
    python -m workers --worker validation
    python -m workers --worker sync

    # Run with debug logging
    python -m workers --debug
"""

import argparse
import asyncio
import logging
import sys
from typing import List

from factory.container import Container
from core.runtime.config import get_config
from .base import WorkerManager
from .validation_worker import ValidationWorker
from .sync_worker import SyncWorker


def setup_logging(debug: bool = False) -> None:
    """Configure logging for workers."""
    level = logging.DEBUG if debug else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

    # Reduce noise from libraries
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("aiormq").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MANTRA Background Workers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available workers:
  validation  - Process decision validation requests
  sync        - Handle embedding and index synchronization

Examples:
  python -m workers                    # Run all workers
  python -m workers --worker validation  # Run validation worker only
  python -m workers --debug            # Run with debug logging
        """
    )

    parser.add_argument(
        "--worker",
        "-w",
        choices=["validation", "sync", "all"],
        default="all",
        help="Worker to run (default: all)"
    )

    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging"
    )

    return parser.parse_args()


async def main() -> None:
    """Main entry point for workers."""
    args = parse_args()
    setup_logging(args.debug)

    logger = logging.getLogger(__name__)
    config = get_config()

    # Check if message queue is enabled
    if not config.feature_rabbitmq_enabled:
        logger.error("RabbitMQ feature is disabled. Enable with FEATURE_RABBITMQ_ENABLED=true")
        sys.exit(1)

    # Initialize container (connects to PostgreSQL, etc.)
    logger.info("Initializing container services...")
    await Container.initialize()
    logger.info("Container initialized")

    # Get message queue
    queue = Container.get_message_queue()
    if not queue:
        logger.error("Failed to initialize message queue")
        sys.exit(1)

    # Get optional services
    cache = Container.get_cache()
    text_search = Container.get_text_search()

    # Create workers
    workers: List = []

    if args.worker in ("validation", "all"):
        workers.append(ValidationWorker(queue, cache))

    if args.worker in ("sync", "all"):
        workers.append(SyncWorker(queue, cache, text_search))

    if not workers:
        logger.error("No workers to run")
        sys.exit(1)

    # Create manager and run
    manager = WorkerManager()
    for worker in workers:
        manager.add_worker(worker)

    logger.info(f"Starting {len(workers)} worker(s)...")

    try:
        await manager.start_all()
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
        await manager.stop_all()
    except Exception as e:
        logger.error(f"Worker error: {e}")
        await manager.stop_all()
        sys.exit(1)
    finally:
        await Container.close_all()


if __name__ == "__main__":
    asyncio.run(main())
