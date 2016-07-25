import argparse
import json
import asyncio
import stream
import pool


class Connection(asyncio.Protocol):
    """Request/response messaging protocol

    This protocol is for generic request/response interaction. It is intended to
    be used symmetrically, i.e. both ends of the connection should use the same
    protocol.

    We assume the data comes in formatted as JSON. If the incoming data is a
    request we assume it has the following fields:
        id (int): Identifies the request. Must be positive.
        method (str): Name of the remote method to call.
        args (list): List of arguments to pass to the remotely called method.
    For example, a request to a calculator's 'add' method might look like this
    on the wire: '{"id": 4, "method": "add", "args": [4, 5]}'. If the incoming
    data is a response to a request we made previously, we assume it has the
    following fields:
        id (int): Must be negative, and in particular must be minus the value of
            the request for which this is the response.
        result (any): The result of the remote method invokation for which this
            message is an answer.

    Attributes:
        stream: Parses incoming bytes and packages them into individual
            messages. Each message is a python dict version of the incoming
            JSON.
        id_pool (MessageIdPool): Provides values to use in our messaging
            protocol's id field.
        pending_requests(dict): Maps message id's to Task's waiting for that
            message's data.
    """
    def __init__(self, loop, stream, id_pool):
        self.loop = loop
        self.stream = stream
        self.id_pool = id_pool
        self.pending_requests = {}  # Request id -> Task

    def connection_made(self, transport):
        print("Connection made")
        self.transport = transport

    def make_outbound_request(self, method, args):
        """Make an outbound request.

        Returns:
            We return a future which is fired when the result of the request is
            ready. This happens after we receive a response message and parse
            it.
        """
        message_id = self.id_pool.get_id()
        message = {  # TODO: Use the data stream to parse outgoing data
            'id': message_id,
            'method': method,
            'args': args}
        self.transport.write(json.dumps(message).encode())
        f = asyncio.Future()
        self.pending_requests[message_id] = f
        return f

    def data_received(self, data):
        """Receive incoming bytes and send to the data stream."""
        messages = self.stream.receive(data.decode())
        for message in messages:
            self.message_received(message)

    def message_received(self, message):
        """Handle a message.

        Inbound requests have the following fields:
            id (int > 0): Message id.
            method (str): name of method to call.
            args (object): key/value pairs of named arguments.
        Inbound responses have the following fields:
            id (int < 0): Id of request for which this is the response.
            result (?): Any data type.
        """
        message_id = message['id']
        if message_id > 0:
            # This is a request
            self.loop.create_task(self.handle_inbound_request(message))
        if message_id < 0:
            # This is a response
            self.handle_response(message)

    async def handle_inbound_request(self, message):
        message_id = message['id']
        method_name = message['method']
        args = message['args']
        if not isinstance(args, (tuple, list)):
            args = (args,)
        method = getattr(self, method_name)
        result = await method(*args)
        response = {'id': -message_id, 'result': result}
        self.transport.write(json.dumps(response).encode())

    def handle_response(self, message):
        message_id = message['id']
        self.id_pool.return_id(-message_id)
        result = message['result']
        # Note that interruption of the thread at this point could be bad,
        # because we returned the message id but haven't set the result
        # for that message's future yet.
        self.pending_requests[-message_id].set_result(result)

    async def add(self, x, y):
        print("Serving add({}, {})".format(x, y))
        z = x + y
        result = await self.make_outbound_request('echo', z)
        return result

    async def echo(self, data):
        print("Serving echo({})".format(data))
        return data


class ConnectionFactory:
    def __init__(self, connection, loop_factory, stream_factory, pool_factory):
        self.connection = connection
        self.loop_factory = loop_factory
        self.stream_factory = stream_factory
        self.pool_factory = pool_factory

    def __call__(self):
        loop = self.loop_factory()
        stream = self.stream_factory()
        pool = self.pool_factory()
        return self.connection(loop, stream, pool)


default_connection_factory = ConnectionFactory(
        Connection,
        asyncio.get_event_loop,
        stream.JsonDataStream,
        pool.MessageIdPool)


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
        'add',
        [1,2])
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

