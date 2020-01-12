import asyncio, json, argparse
from sys import stdout

class Client(asyncio.Protocol):
    def __init__(self, loop, user, **kwargs):
        self.user = user
        self.is_open = False
        self.loop = loop
        self.last_message = ""

    def connection_made(self, transport):
        self.sockname = transport.get_extra_info("sockname")
        self.transport = transport
        self.transport.write(self.user.encode())
        self.is_open = True

    def connection_lost(self, exc):
        self.is_open = False
        self.loop.stop()

    def data_received(self, data):
        while not hasattr(self, "output"): #Wait until output is established
            pass
        if data:
            message = json.loads(data.decode())
            self.process_message(message)       
    
    def process_message(self, message):
        try:
            if message["event"] == "message":
                content = "{timestamp} | {author}: {content}".format(**message)
            elif message["event"] == "servermsg":
                content = "{timestamp} | {author} {content}".format(**message)
            else:
                content = "{timestamp} | {author}: {content}".format(**message)
            
            self.output(content.strip() + '\n')
        except KeyError:
            print("Malformed message, skipping")

    def send(self, data):
        if data and self.user:
            self.last_message = "{author}: {content}".format(author=self.user, content=data)
            self.transport.write(data.encode())

    async def getmsgs(self, loop):
        self.output = self.stdoutput
        self.output("Connected to {0}:{1}\n".format(*self.sockname))
        while True:
            msg = await loop.run_in_executor(None, input, "{}: ".format(self.user)) #Get stdout input forever
            self.send(msg)

    
    def stdoutput(self, data):
        if self.last_message.strip() == data.strip():
            return #Unclouds stdout with duplicate messages (sent and received)
        else:
            stdout.write(data.strip() + '\n')

class HandleClient():
    def __init__(self, login, port=50000):
        self.user = login
        self.loop = asyncio.get_event_loop()
        self.client = Client(self.loop, self.user)
        coro = self.loop.create_connection(lambda: self.client, "127.0.0.1", 50000)
        server = self.loop.run_until_complete(coro)

        asyncio.ensure_future(self.client.getmsgs(self.loop))
        self.loop.run_forever()
        self.loop.close()

if __name__ == "__main__":
    client = HandleClient('Jakub')