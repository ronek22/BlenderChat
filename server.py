import socket
import select
import threading
import sys

class Server:

    HEADER_LENGTH = 10
    IP = "127.0.0.1"

    def __init__(self, port):
        self.PORT = port
        self.configure_server()
        self._running = True
        

    def configure_server(self):
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reconnection
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen()
        self.sockets_list = [self.server_socket]
        self.clients = {}

    def receive_message(self, client_socket):
        try:
            message_header = client_socket.recv(self.HEADER_LENGTH)

            if not message_header:
                return False

            message_length = int(message_header.decode())
            # WARNING SET LENGTH LIMITS
            return {"header": message_header, "data": client_socket.recv(message_length)}
        except:
            return False

    def _run(self):
        while self._running:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            
            for notified_socket in read_sockets:
                if notified_socket == self.server_socket:
                    client_socket, client_address = self.server_socket.accept()

                    user = self.receive_message(client_socket)
                    if user is False: # someone was disconnected
                        continue
                    
                    self.sockets_list.append(client_socket)
                    self.clients[client_socket] = user
                    # BECAUSE FIRST SENDED DATA IS USERNAME
                    print(f"{user['data'].decode()} join channel.\nInfo:{client_address[0]}:{client_address[1]}")

                else:
                    message = self.receive_message(notified_socket)
                    if not message:
                        print(f"{self.clients[notified_socket]['data'].decode()} left channel")
                        self.sockets_list.remove(notified_socket)
                        del self.clients[notified_socket]
                        continue
                    
                    user = self.clients[notified_socket]
                    print(f"{user['data'].decode()} > {message['data'].decode()}")

            for notified_socket in exception_sockets:
                self.sockets_list.remove(notified_socket)
                del self.clients[notified_socket]

    def terminate(self):
        self._running = False

    def run(self):
        self.thread_server = threading.Thread(target=self._run, daemon=True)
        self.thread_server.start()
    
    def close(self):
        self.thread_server.join(10)
        sys.exit(0)

if __name__ == "__main__":
    server = Server(12345)
    server.run()