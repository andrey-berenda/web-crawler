import dataclasses
import enum


class CrawlingRequestStatus(enum.Enum):
    CREATED = 'CREATED'
    STARTED = 'STARTED'
    DONE = 'DONE'
    FAILED = 'FAILED'


@dataclasses.dataclass
class CrawlingRequest:
    url: str
    status: CrawlingRequestStatus
    result: list[str]


_CREATE_QUERY = '''
INSERT INTO crawling_requests (url, status) VALUES (%s, 'CREATED')
ON CONFLICT (url) DO UPDATE SET url = %s
RETURNING url, status, result;
'''

_GET_CREATED = '''
WITH cte AS (
   SELECT id
   FROM   crawling_requests
   WHERE  status = 'CREATED'
   ORDER BY created_at
   LIMIT  1
)
UPDATE crawling_requests
SET status = 'STARTED', updated_at = now()
FROM cte
WHERE cte.id = crawling_requests.id
RETURNING crawling_requests.url,  crawling_requests.status, crawling_requests.result;
'''

_UPDATE_QUERY = '''
UPDATE crawling_requests
SET status = %s, result = %s, updated_at = now()
WHERE url = %s
RETURNING url, status, result;
'''


async def get_or_create_crawling_request(url, conn) -> CrawlingRequest:
    # TODO: Добавить логику по устареванию,
    # то есть если мы страницу просматривали неделю назад, то надо её повторно просмотреть
    # Можно добавить отдельный воркер, который удаляет страницы,
    # которые созданы больше недели назад (или дня или часа)
    async with conn.cursor() as cursor:
        await cursor.execute(_CREATE_QUERY, [url, url])
        row = await cursor.fetchone()
        return CrawlingRequest(row[0], CrawlingRequestStatus(row[1]), row[2])


async def get_next_crawling_request(conn) -> CrawlingRequest | None:
    async with conn.cursor() as cursor:
        await cursor.execute(_GET_CREATED, [])
        row = await cursor.fetchone()
        if row is None:
            return None
        return CrawlingRequest(row[0], CrawlingRequestStatus(row[1]), row[2])


async def update_crawling_request(crawling_request: CrawlingRequest, conn):
    async with conn.cursor() as cursor:
        await cursor.execute(_UPDATE_QUERY, [
            crawling_request.status.value,
            crawling_request.result,
            crawling_request.url,
        ])
