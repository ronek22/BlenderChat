import socket 
import select
import errno
import sys


class Client:

    HEADER_LENGTH = 10
    IP = "127.0.0.1"


    def __init__(self, username, port):
        self.PORT = port
        self.username = username
        self.client_socket = socket.socket()
        self.client_socket.connect((self.IP,self.PORT))
        self.client_socket.setblocking(False) # RECEIVE DONT BE BLOCKING
        self.send_username_data()

    def send_username_data(self):
        username = self.username.encode()
        username_header = f"{len(username):<{self.HEADER_LENGTH}}".encode()
        self.client_socket.send(username_header+username)

    def send_message(self, message):
        message = message.encode()
        message_header = f"{len(message):<{self.HEADER_LENGTH}}".encode()
        self.client_socket.send(message_header + message)
