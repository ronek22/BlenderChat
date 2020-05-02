import zmq
import uuid
from time import sleep
import argparse


class Client:
    def __init__(self, ip, port=5555):
        self.context = zmq.Context().instance()
        self.req = self.context.socket(zmq.REQ)
        self.pub = self.context.socket(zmq.PUB)
        
        self.req.connect(f'tcp://{ip}:{port}')
        self.pub.connect(f'tcp://{ip}:{port-1}')

        self.id = uuid.uuid4().urn[9:]

    def send_using_pub(self, message='Hello'):
        if self.pub: 
            print(f"Client: {self.id}\nSending request to server.")
            self.pub.send_multipart([bytes(self.id, 'utf-8'), bytes(message, 'utf-8')])


    def send_using_req(self, message='Hello'):
        if self.req:
            print(f"Sending message to subscriber: {message}") 
            self.req.send_multipart([bytes(self.id,'utf-8'), bytes(message, 'utf-8')])

            reply = self.req.recv()
            print(f"Received reply: {reply}")

    def test(self):
        for request in range(10):
            print(f"Sending request no. {request}")
            self.req.send_multipart([bytes(self.id, 'utf-8'), b'Hello'])

            # Get reply,
            # If server is not working that maybe blocking, lecturer account, timeout and cancel
            # TODO: TIMEOUT FUNCTION
            reply = self.req.recv()
            print(f"Received reply:  {reply}")

            sleep(.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, required=True)
    args = parser.parse_args()

    client = Client(args.ip)










