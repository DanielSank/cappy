import json


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
