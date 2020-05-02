import zmq
import uuid
from time import sleep

port = 5555
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(f'tcp://188.68.236.117:{port}')
id = uuid.uuid4().urn[9:]

for request in range(10):
    print(f"Sending request no. {request}")
    socket.send_multipart([bytes(id, 'utf-8'), b'Hello'])

    # Get reply,
    # If server is not working that maybe blocking, lecturer account, timeout and cancel
    # TODO: TIMEOUT FUNCTION
    reply = socket.recv()
    print(f"Received reply:  {reply}")

    sleep(.1)