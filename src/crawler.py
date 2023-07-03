import asyncio
import logging
import os
import pathlib
from urllib import parse

import aiohttp
import aiohttp.client_exceptions
from bs4 import BeautifulSoup

from db.crawling_request import CrawlingRequest
from db.crawling_request import CrawlingRequestStatus
from db.crawling_request import get_next_crawling_request
from db.crawling_request import update_crawling_request
from db.page import Page
from db.page import get_page
from db.page import update_page
from db.pool import init_db
from db.pool import pool


def get_int_from_env(name: str, default: int):
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


HTTP_TIMEOUT = get_int_from_env('HTTP_TIMEOUT', 1)
HTTP_RETRY_COUNT = get_int_from_env('HTTP_RETRY_COUNT', 1)
SLEEP_DELAY = get_int_from_env('SLEEP_DELAY', 1)
MAX_CONCURRENT_PROCESSING_URLS = get_int_from_env('MAX_CONCURRENT_PROCESSING_URLS', 5)
COUNT_CRAWLERS = get_int_from_env('COUNT_CRAWLERS', 2)


def get_urls(url, html):
    # noinspection PyProtectedMember
    url = parse.urlparse(url)._replace(query=None)
    soup = BeautifulSoup(html, 'html.parser')
    found = set()
    for link in soup.find_all('a'):
        path = link.get('href')
        if not path:
            continue
        if path.startswith('#'):
            continue

        if not path.startswith('http://') and not path.startswith('https://'):
            p = (pathlib.Path(url.path) / path).resolve()
            # noinspection PyProtectedMember
            path = url._replace(path=str(p)).geturl()
        if path not in found:
            yield path
        found.add(path)


async def get_html(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        for _ in range(HTTP_RETRY_COUNT):
            try:
                async with session.get(url, timeout=HTTP_TIMEOUT) as resp:
                    if 'html' not in resp.headers.getone('Content-Type', ''):
                        return ''
                    return await resp.text()
            except (TimeoutError, aiohttp.ClientError):
                logging.exception(f'Got exception for {url}')
                continue

        # TODO: Либо бросать исключение либо возвращать ''
        return ''


async def process_url(url: str, semaphore: asyncio.Semaphore) -> Page:
    async with semaphore, pool.connection() as conn:
        page = await get_page(url, conn)
        if page.inner_urls:
            return page
        html = await get_html(page.url)
        page.inner_urls = sorted(get_urls(page.url, html))
        await update_page(page, conn)
        return page


async def process_crawling_request(crawling_request: CrawlingRequest) -> CrawlingRequest:
    visited_urls = set()
    to_visit = {crawling_request.url}
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PROCESSING_URLS)

    # Это можно записывать в какую-нибудь очередь и вычитывать
    # оттуда тогда это можно будет делать не на одном хосте
    while to_visit:
        logging.info(f"to_visit: {to_visit}")
        tasks = (
            process_url(url, semaphore)
            for url in to_visit
        )
        # Если записывать в очередь,
        # то тогда visited_urls надо будет записывать в redis
        visited_urls.update(to_visit)
        pages = await asyncio.gather(*tasks)
        to_visit.clear()

        for page in pages:
            for url in page.inner_urls:
                if url not in visited_urls:
                    to_visit.add(url)

    crawling_request.result = sorted(visited_urls)
    crawling_request.status = CrawlingRequestStatus.DONE
    async with pool.connection() as conn:
        await update_crawling_request(crawling_request, conn)
    return crawling_request


async def start_crawling():
    while True:
        async with pool.connection() as conn:
            crawling_request = await get_next_crawling_request(conn)
        if crawling_request is not None:
            await process_crawling_request(crawling_request)
        else:
            await asyncio.sleep(SLEEP_DELAY)


async def start():
    await init_db()
    tasks = (
        start_crawling()
        for _ in range(COUNT_CRAWLERS)
    )
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    # TODO: Add graceful shutdown
    asyncio.run(start())
