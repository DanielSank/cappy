from abc import ABCMeta, abstractmethod


class Calculator(metaclass=ABCMeta):

    def __init__(self, outbound_requester):
        self.outbound_requester = outbound_requester

    @abstractmethod
    def add(self, x, y):
        """Add two numbers."""

    def echo(self, x):
        print("Serving echo({})".format(x))
        return x


class CalculatorAsyncio(Calculator):

    async def add(self, x, y):
        print("Serving add({}, {})".format(x, y))
        z = x + y
        result = await self.outbound_requester({'method': 'echo', 'args': z})
        return result


class CalculatorFutures(Calculator):

    def add(self, x, y):
        print("Serving add({}, {})".format(x, y))
        z = x+y
        f = self.outbound_requester({'method': 'echo', 'args': z})
        return f

