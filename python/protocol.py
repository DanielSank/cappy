import json


class JsonDataStream(object):
    """Consumes bytes and produces JSON objects

    Attributes:
        depth (int): Level of nested '{'. While scanning new data, if depth
            goes to 0, we know we've gotten to the end of a complete JSON
            object.
        buf (str): Data we've seen in the past which wasn't part of a complete
            message.
    """

    def __init__(self):
        self.depth = 0
        self.buf = ''

    def receive(self, data):
        """Process incoming bytes, returning a json object if 

        Args:
            data (string): raw bytes off the wire.

        Returns:
            (list(json object)): List of json objects.
        """
        objects = []
        # In python these are dicts, which can contain anything at all.
        # In a language with static types we'd like to provide information to
        # compiler about the form of these objects.

        start_index = 0
        s = self.buf + data

        for i, char in enumerate(data):
            if char == "{":
                self.depth -= 1
            elif char == "}":
                self.depth += 1
            if self.depth == 0:  # Complete message
                completed = self.buf + data[start_index: i+1]
                self.buf = ''
                objects.append(json.loads(completed))
                # The loads call here produces a python dict with an arbitrary
                # number of fields, etc. In a statically typed language we'd
                # prefer the loads equivalent to produce a more structured
                # result. In particular, we probably can't do _all_ of the
                # unflattening in one step.

                start_index = i+1
        self.buf += data[start_index:]
        return objects


class Protocol(object):
    """Network protocol, handling incoming bytes.

    Attributes:
        stream (Stream): Incoming bytes are fed to the stream, which figures
            out when a complete message has been collected. In the present code
            this is a JsonDataStream.
        connection (Connection): Object representing a network connection. This
            object calls our data_received, and has a write method which we call
            when we have data to send out over the wire.
        implementation: Object providing methods to be called based on incoming
            messages.

    Subclasses must define the class level attribute Implementation. This class
    gets instanced during initialization to create the implementation attribute.
    """

    Implementation = None
    # We instance this class during initialization to make our implementation.

    def __init__(self, connection):
        """Initialize a Protocol.

        Args:
            connection (Connection): See Attributes.
        """
        self.stream = JsonDataStream()
        self.connection = connection
        self.implementation = self.Implementation()

    def data_received(self, data):
        """Handle bytes from the wire.

        Args:
            data (str): Bytes from the wire.
        """
        print("Received data: {}".format(data))
        messages = self.stream.receive(data)
        if len(messages) > 0:
            for message in messages:
                self.handle_message(message)

    def handle_message(self, message):
        """Handle a single complete message."""
        if "result" in message:
            self.handle_inbound_response(message)
        else:
            self.handle_inbound_request(message)

    def handle_inbound_response(self, message):
        """Handle a response by firing the appropriate future."""
        raise NotImplementedError

    def handle_inbound_request(self, message):
        """Handle an incoming message by invoking a capability.

        Args:
            message (json): A JSON object representing a message
        """
        try:
            method_name = message['method']
            request_id = message['id']
            args = message['args']
        except KeyError as e:
            raise  # TODO actually generate an erro message instead

        result = getattr(self.implementation, method_name)(*args)
        # TODO: This call should return a Promise which is fufilled when the
        # result is ready.

        response = {
                "id": request_id,
                "result": result
        }
        self.connection.write(json.dumps(response))
