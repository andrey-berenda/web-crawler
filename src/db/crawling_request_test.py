import uuid

from db.crawling_request import CrawlingRequest
from db.crawling_request import CrawlingRequestStatus
from db.crawling_request import get_next_crawling_request
from db.crawling_request import get_or_create_crawling_request
from db.crawling_request import update_crawling_request


async def test_get_or_create_crawling_request(conn):
    random_string = uuid.uuid4()
    url = f'https://{random_string}'
    async with conn.transaction(force_rollback=True):
        # Act
        crawling_request = await get_or_create_crawling_request(url, conn)

        expected = CrawlingRequest(url, CrawlingRequestStatus.CREATED, [])
        assert crawling_request == expected


async def test_get_next_crawling_request(conn):
    random_string = uuid.uuid4()
    url = f'https://{random_string}'

    async with conn.transaction(force_rollback=True):
        await get_or_create_crawling_request(url, conn)

        # Act
        crawling_requests = [
            await get_next_crawling_request(conn)
            for _ in range(2)
        ]

        expected = CrawlingRequest(url, CrawlingRequestStatus.STARTED, [])
        assert crawling_requests == [expected, None]


async def test_update_crawling_request(conn):
    random_string = uuid.uuid4()
    url = f'https://{random_string}'
    result = ['https://test.com', 'https://test.ru']
    async with conn.transaction(force_rollback=True):
        await get_or_create_crawling_request(url, conn)
        crawling_request = await get_next_crawling_request(conn)
        crawling_request.result = result
        crawling_request.status = CrawlingRequestStatus.DONE

        assert crawling_request.url == url

        # Act
        await update_crawling_request(crawling_request, conn)

        crawling_request = await get_or_create_crawling_request(url, conn)

        expected = CrawlingRequest(url, CrawlingRequestStatus.DONE, result)
        assert crawling_request == expected
