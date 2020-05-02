import zmq
from time import sleep
from pprint import pprint

port = 5555
context = zmq.Context()
socket = context.socket(zmq.REP)
subscriber = context.socket(zmq.SUB)
subscriber.setsockopt(zmq.SUBSCRIBE, b'')
subscriber.bind(f"tcp://0.0.0.0:5554")
socket.bind(f"tcp://0.0.0.0:{port}")
noRequest = 1
# how to bind to random available port
# selected_port = socket.bind_to_random_port('tcp://*')

clients = {}

#region Thoughts
# Serwer musi nasluchiwac
# Skąd wiadomo do jakiego socketu ma wyslać World?
# REQ-REP, pattern działa na zasadzie,
# serwer otrzymuje request (1 na raz) i odpowiada na ten request
# jest to tak jakby operacja atomowa i jest zagwarantowane
# to, że odpowiedz otrzyma adresat
# Wadą jest to, że możliwe jest blockowwanie i nieskonczona petla
# Klientem może zawiesić się podczas wysyłania requesta (?) NIE JESTEM PEWNY CZY TO BLOKUJE
# Bądź serwer podczas wysyłania odpowiedzi
#endregion
while True: 
    message = socket.recv_multipart()
    client_id = message[0].decode()
    clients[client_id] = clients.get(client_id) + 1 if client_id in clients else  1
    print(f"Received message {noRequest} from {client_id}: {message[1].decode()}")

    sleep(.1)

    socket.send_string("World")
    # pprint(clients)
    noRequest+=1
