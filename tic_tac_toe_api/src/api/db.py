"""Async PostgreSQL database utility module."""
import os
import asyncpg

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB   = os.getenv("PG_DB", "tic_tac_toe_db")
PG_USER = os.getenv("PG_USER", "tic_tac_toe_user")
PG_PASS = os.getenv("PG_PASS", "tic_tac_toe_pass")

class Database:
    pool: asyncpg.Pool = None

    # PUBLIC_INTERFACE
    @classmethod
    async def connect(cls):
        if not cls.pool:
            cls.pool = await asyncpg.create_pool(
                user=PG_USER, password=PG_PASS, database=PG_DB, host=PG_HOST, port=PG_PORT,
                min_size=1, max_size=10
            )

    # PUBLIC_INTERFACE
    @classmethod
    async def close(cls):
        if cls.pool:
            await cls.pool.close()

    # PUBLIC_INTERFACE
    @classmethod
    async def get_conn(cls):
        if not cls.pool:
            await cls.connect()
        return cls.pool

    # PUBLIC_INTERFACE
    @classmethod
    async def transaction(cls):
        pool = await cls.get_conn()
        async with pool.acquire() as conn:
            async with conn.transaction():
                yield conn
