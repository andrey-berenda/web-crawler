import uuid

from db.page import Page
from db.page import get_page
from db.page import update_page


async def test_get_page(conn):
    random_string = uuid.uuid4()
    url = f'https://{random_string}'

    async with conn.transaction(force_rollback=True):
        # Act
        page = await get_page(url, conn)

        expected = Page(url, [])
        assert page == expected


async def test_update_page(conn):
    random_string = uuid.uuid4()
    url = f'https://{random_string}'

    async with conn.transaction(force_rollback=True):
        page = await get_page(url, conn)
        inner_urls = ['https://test.com', 'https://test.ru']
        page.inner_urls = inner_urls

        # Act
        await update_page(page, conn)

        page = await get_page(url, conn)

        expected = Page(url, inner_urls)
        assert page == expected
