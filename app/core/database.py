"""
PhinsIQ MongoDB Database Layer
================================

PURPOSE:
    Manages the single MongoDB client connection for the entire application.
    Provides a dependency-injectable database accessor used by all repositories.

WHY A SINGLE CLIENT?
    MongoDB client instances are expensive to create — they establish a connection
    pool (multiple persistent connections) to the database server.

    If every request created a new client:
    - 1000 requests/second = 1000 connection pool creations/second
    - MongoDB would quickly run out of connections
    - Latency would be enormous

    By creating ONE client at application startup and reusing it for every request,
    connection overhead is paid once. The pool handles concurrent requests automatically.

WHAT IS A CONNECTION POOL?
    A connection pool is a set of pre-established database connections held ready.
    When a request needs to query MongoDB, it borrows a connection from the pool,
    uses it, and returns it. This is much faster than creating a new connection.

    Motor (async MongoDB driver) manages this pool automatically.

HOW FASTAPI LIFESPAN WORKS:
    FastAPI uses an "async context manager" called a lifespan to run code:
    - At application STARTUP: Connect to MongoDB, start the pool
    - At application SHUTDOWN: Close connections cleanly

    This ensures:
    1. MongoDB is ready before the first request arrives
    2. Connections are closed properly when the server stops (not abruptly)

USAGE IN REPOSITORIES:
    from app.core.database import get_database
    from motor.motor_asyncio import AsyncIOMotorDatabase

    async def get_institution(institution_id: str) -> dict:
        db = get_database()
        return await db.institutions.find_one({"_id": institution_id})
"""

import certifi
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level client variable.
# WHY MODULE-LEVEL? The client must be accessible to all parts of the application.
# Making it module-level means it's created once and shared.
# WHY OPTIONAL? It starts as None and is set during startup — we cannot connect
# before the application starts.
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb() -> None:
    """
    Establish the MongoDB connection pool at application startup.

    Called once during the FastAPI lifespan startup phase.

    WHY WE VERIFY THE CONNECTION WITH ping:
        Motor is lazy — it doesn't actually connect when AsyncIOMotorClient is created.
        It connects on the first operation. By sending a ping() immediately,
        we verify MongoDB is reachable BEFORE the server starts accepting requests.
        If MongoDB is down, the server fails fast at startup rather than on the
        first user request (which would give a confusing error to the user).
    """
    global _client, _database

    logger.info("mongodb_connecting", url=settings.mongodb_url.split("@")[-1])

    _client = AsyncIOMotorClient(
        settings.mongodb_url,
        # serverSelectionTimeoutMS: How long to wait before giving up on
        # finding a MongoDB server to connect to.
        serverSelectionTimeoutMS=settings.mongodb_timeout * 1000,
        # connectTimeoutMS: How long to wait for a connection to be established.
        connectTimeoutMS=settings.mongodb_timeout * 1000,
        # socketTimeoutMS: How long to wait for a socket operation to complete.
        socketTimeoutMS=settings.mongodb_timeout * 1000,
        # tlsCAFile: Use certifi's trusted CA bundle for TLS verification.
        # WHY THIS IS NEEDED ON macOS + Python 3.14:
        #   macOS stores SSL certificates in its Keychain, not in the standard
        #   OpenSSL certificate store. Python 3.14 (especially when installed
        #   from python.org) does not automatically use Keychain certs.
        #   certifi ships a curated bundle of trusted root CAs (same as browsers use).
        #   This is the recommended fix for MongoDB Atlas SSL errors on macOS.
        tlsCAFile=certifi.where(),
    )

    _database = _client[settings.mongodb_database]

    # Verify connection is actually working before accepting requests.
    await _client.admin.command("ping")

    logger.info(
        "mongodb_connected",
        database=settings.mongodb_database,
    )


async def disconnect_from_mongodb() -> None:
    """
    Close the MongoDB connection pool at application shutdown.

    Called once during the FastAPI lifespan shutdown phase.

    WHY CLEAN SHUTDOWN MATTERS:
        Abruptly killing the process leaves in-flight operations in an
        uncertain state. Motor's close() waits for pending operations to
        complete before closing connections — preventing data corruption.
    """
    global _client

    if _client is not None:
        _client.close()
        logger.info("mongodb_disconnected")


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the active MongoDB database instance.

    WHY NOT JUST USE THE _database GLOBAL DIRECTLY?
        Functions are easier to mock in tests than module-level globals.
        In tests, we can patch get_database() to return a test database.

    Returns:
        AsyncIOMotorDatabase: The phinsiq database instance

    Raises:
        RuntimeError: If called before connect_to_mongodb() (should never happen
                      in normal operation since lifespan handles ordering)
    """
    if _database is None:
        raise RuntimeError(
            "Database not initialized. "
            "connect_to_mongodb() must be called at application startup."
        )
    return _database


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    """
    FastAPI lifespan context manager.

    This is the modern FastAPI way to run startup and shutdown logic.
    It replaces the older @app.on_event("startup") decorators.

    HOW IT WORKS:
        Code BEFORE yield runs at startup.
        Code AFTER yield runs at shutdown.
        The application is ready to receive requests between startup and shutdown.

    TEACHING MOMENT — What is 'async context manager'?
        An async context manager is code that runs before and after a block.
        The 'with' statement in Python uses context managers. The 'async with'
        statement uses async context managers (they can await async operations).
        @asynccontextmanager converts a generator function into a context manager.

    Args:
        app: The FastAPI application instance (passed automatically by FastAPI)
    """
    # ---- STARTUP ----
    await connect_to_mongodb()

    # 'yield' hands control back to FastAPI, which starts serving requests
    yield

    # ---- SHUTDOWN ----
    await disconnect_from_mongodb()
