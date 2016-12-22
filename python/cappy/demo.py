import argparse
import asyncio

from cappy.calculator import CalculatorAsyncio as Calculator
import cappy.stream as stream
import cappy.pool as pool


class Protocol:

    def __init__(self, writer, future_factory):
        self.stream = stream.Stream(
            stream.HeaderByteStream(2),
            stream.JSONParser())
        self.id_pool = pool.MessageIdPool()
        self.pending_requests = {}  # id (int) -> Future
        self._writer = writer
        self.future_factory = future_factory

        self.implementation = Calculator(self.make_outbound_request)

    def is_inbound_request(self, message):
        """Return True if the message is an inbound request."""
        return message['id'] > 0

    def is_response(self, message):
        """Return True if the message is a response."""
        return message['id'] < 0

    def data_received(self, data):
        """Convert incoming bytes to a list of messages."""
        return self.stream.receive(data)

    def make_outbound_request(self, message):
        message_id = self.id_pool.get_id()
        message['id'] = message_id
        print("Making outbound request on method {} with "
              "args {} and id {}".format(
                  message['method'], message['args'], message['id']))
        self.write(self.stream.pack_message(message))
        f = self.future_factory()
        self.pending_requests[message_id] = f
        return f

    async def handle_inbound_request(self, message):
        message_id = message['id']
        method_name = message['method']
        args = message['args']
        if not isinstance(args, (tuple, list)):
            args = (args,)
        method = getattr(self.implementation, method_name)
        result = await asyncio.coroutine(method)(*args)
        response = {'id': -message_id, 'result': result}
        self.write(self.stream.pack_message(response))

    def handle_response(self, message):
        result = message['result']
        message_id = message['id']
        print('handling response to message {} with result {}'.format(
            -message_id, result))
        self.pending_requests[-message_id].set_result(result)
        self.id_pool.return_id(-message_id)
        del self.pending_requests[-message_id]

    def write(self, data):
        self._writer(data)


class Connection(asyncio.Protocol):
    """Request/response messaging protocol"""

    def __init__(self, loop, protocol_class):
        self.loop = loop
        self.protocol_class = protocol_class
        self.protocol = None

    def connection_made(self, transport):
        print("Connection made")
        self.transport = transport
        self.protocol = self.protocol_class(transport.write, asyncio.Future)

    def make_outbound_request(self, data):
        """Make an outbound request.

        This function should be awaited, as it may make outgoing requests, which
        are asynchronous. Note that this is kosher because we return a future.

        Returns:
            We return a future which is fired when the result of the request is
            ready. This happens after we receive a response message and parse
            it.
        """
        return self.protocol.make_outbound_request(data)

    def data_received(self, data):
        """Convert incoming bytes to messages and dispatch them."""
        messages = self.protocol.data_received(data)
        for m in messages:
            if self.protocol.is_inbound_request(m):
                self.loop.create_task(self.protocol.handle_inbound_request(m))
            elif self.protocol.is_response(m):
                self.protocol.handle_response(m)


class ConnectionFactory:

    def __init__(self, protocol_class, loop_factory):
        self.protocol_class = protocol_class
        self.loop_factory = loop_factory

    def __call__(self):
        loop = self.loop_factory()
        return Connection(loop, self.protocol_class)


default_connection_factory = ConnectionFactory(
    Protocol,
    asyncio.get_event_loop)


async def main_server(loop, connection_factory, done, host, port):
    server = await loop.create_server(
        connection_factory,
        host,
        port)
    print("Server created. Listening on {}:{}".format(host, port))
    await done.wait()
    server.close()
    await server.wait_closed()
    print("Server closed")


async def main_client(loop, connection_factory, done, host, port):
    transport, connection = await loop.create_connection(
        connection_factory,
        host,
        port)
    print("Connection created at {}:{}".format(host, port))
    result = await connection.make_outbound_request(
        {'method': 'add', 'args': [1, 2]})
    print("Result: {}".format(result))
    await done.wait()
    print("connection should be closed here")


def main(host, port, as_server):
    if as_server:
        main = main_server
    else:
        main = main_client

    loop = asyncio.get_event_loop()
    done = asyncio.Event()

    future = loop.create_task(main(
        loop,
        default_connection_factory,
        done,
        host,
        port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    done.set()
    loop.run_until_complete(future)
    loop.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test asyncio server')
    parser.add_argument('--host',
                        '-ho',
                        default='localhost',
                        help="Sets host address")
    parser.add_argument('--port',
                        '-p',
                        default=12344,
                        help="Sets connection port")
    server_group = parser.add_mutually_exclusive_group(required=True)
    server_group.add_argument('--server',
                              '-s',
                              dest='as_server',
                              action='store_true',
                              help="Run in server mode")
    server_group.add_argument('--client',
                              '-c',
                              dest='as_server',
                              action='store_false',
                              help="Run in client mode")
    parser.set_defaults(as_server=False)
    args = parser.parse_args()
    host, port, as_server = args.host, args.port, args.as_server

    main(host, port, as_server)
