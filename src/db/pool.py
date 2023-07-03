import os

from psycopg_pool import AsyncConnectionPool

# TODO: читать из секретов или из os.getenv
DB_HOST = os.getenv('DB_HOST', 'localhost')
pool = AsyncConnectionPool(f"host={DB_HOST} dbname=web_crawler user=postgres", open=False)

INIT_DB_QUERIES = [
    '''
    CREATE TABLE IF NOT EXISTS  pages
    (
        id         BIGSERIAL PRIMARY KEY,
        url        text unique                      not null,
        inner_urls text[]      default '{}'::text[] not null,
        created_at timestamptz default now()        not null
    );
    ''',

    '''
    CREATE TABLE IF NOT EXISTS crawling_requests
    (
        id         BIGSERIAL PRIMARY KEY,
        url        text unique                      not null,
        status     text                             not null,
        result     text[]      default '{}'::text[] not null,
        created_at timestamptz default now()        not null,
        updated_at timestamptz default now()        not null
    );
    ''',
    '''
    CREATE INDEX IF NOT EXISTS crawling_requests_created_idx ON crawling_requests(created_at);
    '''
]


async def init_db():
    await pool.open(wait=True)
    async with pool.connection() as conn:
        for query in INIT_DB_QUERIES:
            await conn.execute(query)
