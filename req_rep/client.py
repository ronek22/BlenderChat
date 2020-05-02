import zmq
import uuid
from time import sleep
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--ip', type=str, required=True)
args = parser.parse_args()

port = 5555
context = zmq.Context()
req = context.socket(zmq.REQ)
req.connect(f'tcp://{args.ip}:{port}')

pub = context.socket(zmq.PUB)
pub.connect(f'tcp://{args.ip}:{port-1}')

id = uuid.uuid4().urn[9:]

def send_using_req(message='Hello'):
    if req: 
        print(f"Client: {id}\nSending request to server.")
        socket.send_multipart([bytes(id, 'utf-8'), bytes(message, 'utf-8')])

def send_using_pub(message='Hello'):
    if pub:
        print(f"Sending message to subscriber: {message}") 
        pub.send_multipart([bytes(id,'utf-8'), bytes(message, 'utf-8')])

        reply = socket.recv()
        print(f"Received reply: {reply}")

def test():
    for request in range(10):
        print(f"Sending request no. {request}")
        socket.send_multipart([bytes(id, 'utf-8'), b'Hello'])

        # Get reply,
        # If server is not working that maybe blocking, lecturer account, timeout and cancel
        # TODO: TIMEOUT FUNCTION
        reply = socket.recv()
        print(f"Received reply:  {reply}")

        sleep(.1)




