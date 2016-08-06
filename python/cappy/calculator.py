import protocol
import network


class Calculator(object):
    @staticmethod
    def square(x):
        return x**2


class MyProtocol(protocol.Protocol):
    Implementation = Calculator


def main(host='localhost', port=8083):
    m = {}  # file descriptor -> Asyncable
    reactor = network.Reactor(m)
    network.Dispatcher(host, port, m, MyProtocol)
    reactor.run()


if __name__=='__main__':
    main()
