import socket
import select
import time


class Reactor(object):
    """Asynchronous loop.

    Attributes:
        m (dict): Map from file descriptors to objects who may wish to sign up
            for select.These objects must implement the Asyncable interface.
            See Dispatcher and Connection for examples.
        timeout_s (float): Timeout used in each select call, in seconds.
    """

    def __init__(self, m, timeout_s=0):
        """Initialize a Reactor

        Args:
            m (dict): See attributes.
            timeout_s (float): Select loop timeout in seconds.
        """
        self.m = m  # fileno -> object
        self.timeout_s = timeout_s
        self.running = False

    def run(self):
        self.running = True
        while self.m:
            self.do_select_iteration()
        print("Reactor exiting.")

    def do_select_iteration(self):
        """Excecute one trip around the select loop.

        We check whether or not each element in the map wishes to sign up for
        reading and/or writing. If nobody wants to read or write, we sleep for
        the timeout and return. If someone wants to read/write, we select on
        their file descriptor. Once select returns, we call handle_read or
        handle_write as appropriate.
        """
        to_read = []
        to_write = []
        for fileno, obj in self.m.items():
            if obj.writable():
                to_write.append(fileno)
            if obj.readable():
                to_read.append(fileno)

        if [] == to_read == to_write:
            time.sleep(self.timeout_s)
            return
        # If nobody wants to read or write, then sleep for timeout. This is
        # needed because select() doesn't allow all empty lists as arguments.

        fr, fw, fe = select.select(to_read, to_write, [], self.timeout_s)
        # Ask the OS to block our program until somethings's ready for I/O

        for r in fr:
            self.m[r].handle_read()
        for w in fw:
            self.m[w].handle_write()


class Asyncable(object):
    """Interface provided by objects participating with a Reactor."""

    def readable(self):
        """Should I sign up to accept incoming data?"""

    def writeable(self):
        """Do I have data to write?"""

    def handle_read(self):
        """Called when Reactor detects that we can read without blocking."""

    def handle_write(self):
        """Called when Reactor detects that we can write without blocking."""

    def fileno(self):
        """Get my file descriptor."""


class Dispatcher(Asyncable):
    """Listens for incoming connections and creates Connections.

    Attributes:
        m (dict): The fileno -> Asyncable map of the Reactor managing this
                  Dispatcher's I/O.
        protocol_class: The class representing
    """

    def __init__(self, host, port, m, protocol_class, socket=None):
        """Initialize a Dispatcher.

        Args:
            host (str): IP address of host, i.e. 'localhost' or '192.168.0.1'.
            port (int): Port on which to listen for new connections.
            m (dict): The map of the Reactor handling our select call.
            protocol_class (Protocol): The protocol class used for new
                connections.
            socket (socket.socket): A TCP socket to use for listening. If None
                (the default), we make a new one on initialization.
        """
        self.m = m
        self.protocol_class = protocol_class
        if socket is None:
            socket = self.make_socket()
        self.socket = socket
        self.socket.bind((host, port))
        print("Serving on {}".format(self.socket.getsockname()))
        self.socket.listen(1)
        self.m[self.fileno()] = self

    # Asyncable interface
    def readable(self):
        return True

    def writable(self):
        return False

    def handle_read(self):
        """Handle an incoming connection by creating a new Connection."""
        (conn_sock, client_address) = self.socket.accept()
        print("New connection accepted from {} {}".format(*client_address))
        c = Connection(conn_sock, self.m, self.protocol_class)

    def handle_write(self):
        raise RuntimeError("Unreachable")

    def fileno(self):
        return self.socket.fileno()
    ###

    def make_socket(self):
        """Get a new TCP socket."""
        family = socket.AF_INET
        socket_type = socket.SOCK_STREAM
        sock = socket.socket(family, socket_type)
        sock.setblocking(0)
        return sock


class Connection(Asyncable):
    """A network connection, managed by a Reactor.

    Attributes:
        socket (socket.socket): The TCP socket used by this connection.
        m (dict): Map from file descriptors to Asyncables. We add ourself to
            this map at initialization.
        protocol (Protocol): The thing that consumes incoming data and gives us
            data to write out to the network.
        write_buf (str): Buffer of bytes to be written out over the wire.
    """
    SEND_CHUNK_SIZE = 1024
    READ_CHUNK_SIZE = 1024

    def __init__(self, socket, m, protocol_class):
        self.socket = socket
        m[self.fileno()] = self
        self.m = m
        self.protocol = protocol_class(self)
        self.write_buf = ''

    def write(self, data):
        """Protocol calls this method to send data.

        Args:
            data (str): Bytes to write over the wire.
        """
        self.write_buf += data

    # Asyncable interface
    def readable(self):
        return True

    def writable(self):
        return len(self.write_buf) > 0

    def handle_read(self):
        data = self.socket.recv(self.READ_CHUNK_SIZE)
        if len(data) == 0:  # Socket is closed by other side.
            self.close()
            return
        self.protocol.data_received(data)

    def handle_write(self):
        sent = self.socket.send(self.write_buf[:self.SEND_CHUNK_SIZE])
        self.write_buf = self.write_buf[sent:]

    def fileno(self):
        return self.socket.fileno()
    ###

    def close(self):
        """Cose the socket and unregister from the Reactor."""
        print("Connection closing")
        # TODO: Provide information about _which_ connection is closing.
        del self.m[self.fileno()]
        self.socket.close()
