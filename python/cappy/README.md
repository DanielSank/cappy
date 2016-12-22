So far, this package contains only some basic demo code.
However, that code might be very interesting to beginners!

`client_server_asyncio.py` demonstrates how to write a fully asynchronous RPC system in python 3 using `asyncio`.
To run in server mode:
```
python client_server_asyncio.py --server --port=<your favorite port>
```
Then in a separate shell, run in client mode:
```
python client_server_asyncio.py --client --port=<same port as server>
```
You'll see some stuff printed out, indicating that the client and server have exchanged a few RPC calls!
Note that the only difference between "server" and "client" here is that the server listens for incoming connecitons.
Once the connection is established, the RPC system is completely symmetric.

For fun, we've also implemented the RPC system entirely from scratch, i.e. without using asyncio.
Instead, we use our own event loop (see [reactor.py](https://github.com/DanielSank/cappy/blob/master/python/cappy/reactor.py)) based on the sytem call `select`.
To run this home-made version as a server (using port `12344`):
```
python server_futures.py
```
You can then run the asyncio client to see it work.
