import argparse
import asyncio

import json
import stream
import pool


class Protocol:
    def __init__(self):
        self.stream = stream.JsonDataStream()
        self.id_pool = pool.MessageIdPool()
        self.pending_requests = {}  # id (int) -> Future

    def _pack_outbound_request_message(self, message_id, data):
        """Convert request message data to bytes."""
        method = data['method']
        args = data['args']
        return json.dumps(
                {'id': message_id, 'method': method, 'args': args}).encode()

    def is_inbound_request(self, message):
        """Return True if the message is an inbound request."""
        return message['id'] > 0

    def is_response(self, message):
        """Return True if the message is a response."""
        return message['id'] < 0

    def data_received(self, data):
        """Convert incoming bytes to a list of messages."""
        return self.stream.receive(data.decode())

    def make_outbound_request(self, data, transport):
        message_id = self.id_pool.get_id()
        transport.write(self._pack_outbound_request_message(
            message_id, data))
        f = asyncio.Future()
        self.pending_requests[message_id] = f
        return f

    async def handle_inbound_request(self, message, transport, implementation):
        message_id = message['id']
        method_name = message['method']
        args = message['args']
        if not isinstance(args, (tuple, list)):
            args = (args,)
        method = getattr(implementation, method_name)
        result = await asyncio.coroutine(method)(*args)
        response = {'id': -message_id, 'result': result}
        transport.write(json.dumps(response).encode())

    def handle_response(self, message):
        result = message['result']
        message_id = message['id']
        self.pending_requests[-message_id].set_result(result)
        self.id_pool.return_id(-message_id)
        del self.pending_requests[-message_id]


class Calculator:
    def __init__(self, outbound_requester):
        self.outbound_requester = outbound_requester

    async def add(self, x, y):
        print("Serving add({}, {})".format(x, y))
        z = x + y
        result = await self.outbound_requester({'method': 'echo', 'args': z})
        return result

    def echo(self, data):
        print("Serving echo({})".format(data))
        return data


class Connection(asyncio.Protocol):
    """Request/response messaging protocol"""

    def __init__(self, loop, protocol):
        self.loop = loop
        self.protocol = protocol
        self.implementation = Calculator(self.make_outbound_request)

    def connection_made(self, transport):
        print("Connection made")
        self.transport = transport

    def make_outbound_request(self, data):
        """Make an outbound request.

        This function should be awaited, as it may make outgoing requests, which
        are asynchronous. Note that this is kosher because we return a future.

        Returns:
            We return a future which is fired when the result of the request is
            ready. This happens after we receive a response message and parse
            it.
        """
        return self.protocol.make_outbound_request(data, self.transport)

    def data_received(self, data):
        """Convert incoming bytes to messages and dispatch them."""
        messages = self.protocol.data_received(data)
        for m in messages:
            if self.protocol.is_inbound_request(m):
                self.loop.create_task(
                    self.protocol.handle_inbound_request(
                        m, self.transport, self.implementation))
            elif self.protocol.is_response(m):
                self.protocol.handle_response(m)


class ConnectionFactory:
    def __init__(self, protocol_class, loop_factory):
        self.protocol_class = protocol_class
        self.loop_factory = loop_factory

    def __call__(self):
        loop = self.loop_factory()
        protocol = self.protocol_class()
        return Connection(loop, protocol)


default_connection_factory = ConnectionFactory(
        Protocol,
        asyncio.get_event_loop)


async def main_server(connection_factory, done, host, port):
    server = await loop.create_server(
        connection_factory,
        host,
        port)
    print("Server created. Listening on {}:{}".format(host, port))
    await done.wait()
    server.close()
    await server.wait_closed()
    print("Server closed")


async def main_client(connection_factory, done, host, port):
    transport, connection = await loop.create_connection(
        connection_factory,
        host,
        port)
    print("Connection created at {}:{}".format(host, port))
    result = await connection.make_outbound_request(
        {'method': 'add', 'args': [1,2]})
    print("Result: {}".format(result))
    await done.wait()
    print("connection should be closed here")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test asyncio server')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=12344)
    server_group = parser.add_mutually_exclusive_group(required=False)
    server_group.add_argument(
        '--server', dest='as_server', action='store_true')
    server_group.add_argument(
        '--client', dest='as_server', action='store_false')
    parser.set_defaults(as_server=False)
    args = parser.parse_args()
    host, port, as_server = args.host, args.port, args.as_server

    if as_server:
        main = main_server
    else:
        main = main_client

    loop = asyncio.get_event_loop()
    done = asyncio.Event()
    future = loop.create_task(main(
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

