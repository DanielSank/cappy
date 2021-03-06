import socket


from cappy.calculator import CalculatorFutures as Calculator
from cappy.future import Future, call_as_future
import cappy.demo_protocol as cprotocol
from cappy.reactor import Handler, Reactor


def get_listen_socket(host, port):
    """Get a socket that listens for incoming connections.

    Args:
        host (str): Hostname, i.e. 'localhost'.
        port (int): Port on which to listen for incoming connections.

    Returns (socket): A socket listening for connections on the given host and
        port.
    """
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.bind((host, port))
    listen_socket.listen(1)
    return listen_socket


def make_connection_handler(connection_made_callback, host, port):
    """Get a connection handler."""
    listen_socket = get_listen_socket(host, port)
    connection_handler = ConnectionHandler(
            listen_socket,
            connection_made_callback)
    return connection_handler


class ConnectionHandler(Handler):
    """A handler representing a listening socket.

    Attributes;
        socket (socket): The socket this handler uses to listen for incoming
            connections.
        connection_made (function): When a new connection comes in, we call this
            function with the new socket and address as arguments. Typically,
            this function is the connection_made method of a server.
    """
    def __init__(self, socket, connection_made):
        self.socket = socket
        self.connection_made = connection_made

    def register_as_reader(self):
        return True

    def register_as_writer(self):
        return False

    def read(self):
        socket, addr = self.socket.accept()
        self.connection_made(socket, addr)

    def write(self):
        raise RuntimeError("Unreachable")

    def fileno(self):
        return self.socket.fileno()

    def close(self):
        self.socket.close()


class Protocol(cprotocol.Protocol):

    def handle_inbound_request(self, message):
        message_id = message['id']
        method_name = message['method']
        args = message['args']
        if not isinstance(args, (tuple, list)):
            args = (args,)
        method = getattr(self.implementation, method_name)
        future = call_as_future(method, *args)
        def callback(result):
            response = {'id': -message_id, 'result': result}
            self.write(self.stream.pack_message(response))
        future.add_callback(callback)


class ClientHandler(Handler):
    """A handler representing a single client.

    Attributes:
        socket (socket): The socket through which we communicate with the
            client.
        addr (string): The client's address.
        data_received (function): Function to call when we receive data from the
            client.
        connection_closed (function): Function to call when the connection to
            the client is closed.
        buf (str): Data buffer containing bytes to be sent to the client.
    """
    def __init__(self, socket, addr, connection_closed):
        self.socket = socket
        self.addr = addr
        self.connection_closed = connection_closed
        self.buf = b''
        self.protocol = Protocol(self.add_to_buf, Future, Calculator)

    def add_to_buf(self, data):
        self.buf += data

    def register_as_reader(self):
        return True

    def register_as_writer(self):
        return len(self.buf) > 0

    def read(self):
        data = self.socket.recv(1024)
        if len(data) == 0:  # Socket is closed
            self.connection_closed(self)
        messages = self.protocol.data_received(data)
        for m in messages:
            if self.protocol.is_inbound_request(m):
                    self.protocol.handle_inbound_request(m)
            elif self.protocol.is_response(m):
                self.protocol.handle_response(m)

    def write(self):
        num_bytes_sent = self.socket.send(self.buf)
        self.buf = self.buf[num_bytes_sent:]

    def fileno(self):
        return self.socket.fileno()

    def close(self):
        self.socket.close()


def main():
    reactor = Reactor()

    def connection_closed(handler):
        reactor.remove_handler(handler)

    def connection_made(new_socket, addr):
        reactor.add_handler(ClientHandler(new_socket, addr, connection_closed))

    connection_handler =  make_connection_handler(
            connection_made,
            'localhost',
            12344)

    reactor.add_handler(connection_handler)
    reactor.run()


if __name__ == "__main__":
    main()

