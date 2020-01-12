import asyncio
import json
from datetime import datetime

class ChatServerProtocol(asyncio.Protocol):
    def __init__(self, connections, users):
        self.connections = connections
        self.users = users
        self.peername = ""
        self.user = None

    def connection_made(self, transport):
        self.connections += [transport]
        self.peername = transport.get_extra_info('sockname')
        self.transport = transport

    def connection_lost(self, exc):
        if isinstance(exc, ConnectionResetError):
            self.connections.remove(self.transport)
        else:
            print(exc)
        err = "{}:{} disconnected".format(*self.peername)
        print(err)
        for connection in self.connections:
            connection.write(message) # Send to all info about lost connection

    def data_received(self, data):
        if data:
            if not self.user:
                user = data.decode()
                if not user.isalpha():
                    self.transport.write(self.make_mgs("Your name must be alphanumeric", "[Server]", "servermsg"))
                    self.transport.close()
                else:
                    self.user = data.decode()
                    print('{} connected ({}:{})'.format(self.user, *self.peername))
                    msg = '{} connected ({}:{})'.format(self.user, *self.peername)
                    message = self.make_msg(msg, "[Server]", "servermsg")
                    
                    for connection in self.connections:
                        connection.write(message)
            else:
                message = data.decode()
                print(f"{self.user}: {message}")
                msg = self.make_msg(message, self.user)
                for connection in self.connections:
                    connection.write(msg)

        else:
            msg = self.make_msg("Sorry! You sent a message without a name or data, it has not been sent.", "[Server]", "servermsg")
            self.transport.write(msg)

    def make_msg(self, message, author, *event):
            msg = dict()
            msg["content"] = message
            msg["author"] = author
            time = datetime.utcnow()
            msg["timestamp"] = "{hour}:{minute}:{sec}".format(hour=str(time.hour).zfill(2),
                                                              minute=str(time.minute).zfill(2),
                                                              sec=str(time.second).zfill(2))
            if event:
                msg["event"] = event[0]
            else:
                msg["event"] = "message"
            return json.dumps(msg).encode()

class Server():
    def __init__(self, addr="127.0.0.1", port=50000):
        self.addr, self.port = addr, port

        self.connections = []
        self.users = dict()

        self.loop = asyncio.get_event_loop()
        self.server = self.create_and_start_server()


    def create_and_start_server(self):
        coro = self.loop.create_server(lambda: ChatServerProtocol(connections, users), self.addr, self.port)
        server = self.loop.run_until_complete(coro)
        print('Serving on {}:{}'.format(*server.sockets[0].getsockname()))
        # self.loop.run_forever()
        return server

    def close_server(self):
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.loop.close()

        
# if __name__ == "__main__":
#     s = Server()
#     while True:
#         pass

