from abc import ABCMeta, abstractmethod
import select


class Reactor:
    """An event loop.

    The Reactor (so called because it reacts to network activity), is an event
    loop which notifies handlers when they have data ready to be read. Each
    handler must have the interface described by the Handler class above.

    The magic bit of the Reactor is the system call 'select'. Select takes two
    arguments, a list of readers and a list of writers. The call returns when
    at least one of the readers or writers can read or write without blocking.
    See the documentation for select for details.
    """
    def __init__(self):
        self.fileno_map = {}  # fileno -> Handler

    def add_handler(self, handler):
        self.fileno_map[handler.fileno()] = handler

    def remove_handler(self, handler):
        del self.fileno_map[handler.fileno()]

    def run(self):
        """Run the reactor (i.e. event loop).

        Each time around the loop, we find out which of our handlers wants to
        register as a reader or writer. When then pass the readers and writers
        to select, and block until one or more of them is ready for I/O. Then,
        we call their read() or write() methods as appropriate.
        """
        try:
            while 1:
                readers = []
                writers = []
                for fileno, elem in self.fileno_map.items():
                    if elem.register_as_reader():
                        readers.append(fileno)
                    if elem.register_as_writer():
                        writers.append(fileno)

                readers_ready, writers_ready, _ = select.select(
                        readers, writers, [])
                for reader in readers_ready:
                    self.fileno_map[reader].read()
                for writer in writers_ready:
                    self.fileno_map[writer].write()
        except:
            for handler in self.fileno_map.values():
                handler.close()
                raise


class Handler(metaclass=ABCMeta):
    """A handler for the Reactor.

    See the Reactor class for an explanation of what Handlers do.
    """
    @abstractmethod
    def register_as_reader(self):
        """Return True if I should sign up for reading, False otherwise."""

    @abstractmethod
    def register_as_writer(self):
        """Return True if I should sign up for writing, False otherwise."""

    @abstractmethod
    def read(self):
        """Called by reactor when I can read without blocking."""

    @abstractmethod
    def write(self):
        """Called by reactor when I can write without blocking."""

    @abstractmethod
    def fileno(self):
        """Return my file descriptor.

        Usually, return the fileno of a socket I represent.
        """

