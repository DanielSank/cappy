import json


class ByteStream:
    HEADER_LENGTH = 2

    def __init__(self):
        self.buf = b''
        self.reading_header = True
        self.payload_length = None

    def receive(self, b):
        """Take bytes from the wire and return a complete message if avilable.

        Args:
            b (bytes): Some bytes from the wire.

        Returns:
            list of message strings.
        """
        self.buf = self.buf + b
        byte_frames= []

        while 1:
            if not self.reading_header and len(self.buf) >= self.payload_length:
                byte_frames.append(self.buf[0:self.payload_length])
                self.buf = self.buf[self.payload_length:]
                self.reading_header = True

            elif self.reading_header and len(self.buf) >= self.HEADER_LENGTH:
                self.payload_length = int.from_bytes(
                    self.buf[0:self.HEADER_LENGTH], 'big')
                self.buf = self.buf[self.HEADER_LENGTH:]
                self.reading_header = False
            else:
                break
        return byte_frames


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

    def clear(self):
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
