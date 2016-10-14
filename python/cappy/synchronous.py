"""
To test this, in one shell do
$ python demo.py --server
and then in another shell do
$ python crap.py
"""


import asyncio
import functools
import demo


def syncify(f):
    def f_sync(*args, **kwargs):
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(asyncio.ensure_future(
            f(*args, **kwargs)))
        return result
    return f_sync


async def echo_async(connection, data):
    result = await connection.make_outbound_request(
        {'method': 'echo', 'args': [data]})
    return result


class SynchronousClient:
    def __init__(self, connection):
        self.connection = connection

    def echo(self, data):
        return functools.partial(syncify(echo_async), self.connection)(data)


async def get_connection(loop):
    t, c = await loop.create_connection(
        demo.default_connection_factory,
        'localhost',
        12344)
    return c


def main():
    loop = asyncio.get_event_loop()
    connection = syncify(get_connection)(loop)
    cxn = SynchronousClient(connection)
    result = cxn.echo('test data')
    print("Echo result: {}".format(result))


if __name__ == '__main__':
    main()
