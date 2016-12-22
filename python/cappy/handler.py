from abc import ABCMeta, abstractmethod


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

