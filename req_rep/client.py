import zmq
import uuid
from time import sleep
import argparse





if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, required=True)
    args = parser.parse_args()

    port = 5555
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f'tcp://{args.ip}:{port}')
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