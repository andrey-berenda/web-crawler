import dataclasses
import psycopg


@dataclasses.dataclass
class Page:
    url: str
    inner_urls: list[str]


_GET_PAGE_QUERY = '''
INSERT INTO pages (url) VALUES (%s)
ON CONFLICT (url) DO UPDATE SET url = %s
RETURNING url, inner_urls, created_at;
'''

_UPDATE_PAGE_QUERY = '''
UPDATE pages
SET inner_urls = %s, created_at = now()
WHERE url = %s;
'''


async def get_page(url: str, conn: psycopg.AsyncConnection) -> Page:
    # TODO: Добавить логику по устареванию,
    # то есть если мы страницу просматривали неделю назад, то надо её повторно просмотреть
    # Можно добавить отдельный воркер, который удаляет страницы,
    # которые созданы больше недели назад (или дня или часа)
    async with conn.cursor() as cursor:
        await cursor.execute(_GET_PAGE_QUERY, [url, url])
        row = await cursor.fetchone()
        return Page(row[0], row[1])


async def update_page(page: Page, conn: psycopg.AsyncConnection) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(_UPDATE_PAGE_QUERY, [page.inner_urls, page.url])
