import asyncio
import threading
from aiohttp import web


def aiohttp_server():
    def say_hello(request):
        return web.Response(text='Hello, world')

    app = web.Application()
    app.add_routes([web.get('/', say_hello)])
    runner = web.AppRunner(app)
    return runner


def run_server(runner):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, 'localhost', 8080)
    loop.run_until_complete(site.start())
    loop.run_forever()

