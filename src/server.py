import json

from aiohttp import web

from db.crawling_request import get_or_create_crawling_request
from db.pool import pool

routes = web.RouteTableDef()

INDEX = '''
<!DOCTYPE html>
<html>
<body>

<h2>HTML Forms</h2>

<form action="/create-crawling-request">
  <input type="text" id="url" name="url"><br>
  <input type="submit" value="Go">
</form> 

</body>
</html>
'''

TEST_PAGE = '''
<!DOCTYPE html>
<html>
<body>
<a href="/test-page-1">Main</a>
<a href="/test-page-2">Test page</a>
</body>
</html>
'''

TEST_PAGE_1 = '''
<!DOCTYPE html>
<html>
<body>
<a href="/test-page-2">Test page</a>
</body>
</html>
'''

TEST_PAGE_2 = '''
<!DOCTYPE html>
<html>
<body>
</body>
</html>
'''


@routes.get('/')
async def index(request):
    return web.Response(text=INDEX, content_type='text/html', charset='UTF-8')


@routes.get('/test-page')
async def test_page(request):
    return web.Response(text=TEST_PAGE, content_type='text/html', charset='UTF-8')


@routes.get('/test-page-1')
async def test_page(request):
    return web.Response(text=TEST_PAGE_1, content_type='text/html', charset='UTF-8')


@routes.get('/test-page-2')
async def test_page(request):
    return web.Response(text=TEST_PAGE_2, content_type='text/html', charset='UTF-8')


@routes.get('/create-crawling-request')
async def create_crawling_request(request):
    url = request.query.get('url')
    if url is None:
        return web.Response(status=400, text='Bad request')
    async with pool.connection() as conn:
        crawling_request = await get_or_create_crawling_request(url, conn)
    data = {
        'url': crawling_request.url,
        'status': crawling_request.status.value,
        'result': crawling_request.result,
    }
    return web.Response(text=json.dumps(data), content_type='text/html', charset='UTF-8')


async def start_app():
    app = web.Application()
    app.add_routes(routes)
    await pool.open(wait=True)
    return app


if __name__ == '__main__':
    start_app()
