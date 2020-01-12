from aiohttp import web
routes = web.RouteTableDef()

class Server:
    def __init__(self, port):
        self.port = port
        self.app = web.Application()
        self.app.add_routes(routes)

    @routes.get('/')
    async def hello(request):
        return web.Response(text="Hello, world")

    def run(self):
        web.run_app(self.app, host='localhost', port=self.port)

if __name__ == "__main__":
    server = Server()
    server.run()