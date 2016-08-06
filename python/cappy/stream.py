import json


class Stream:
    def __init__(self, binary_stream, message_parser):
        self.bs = binary_stream
        self.mp = message_parser

    def receive(self, data):
        """Receive incoming bytes and produce message objects.

        Args:
            data (bytes): Bytes off the wire.

        Returns:
            (list): message objects, e.g. dicts representing JSON messages.
        """
        binary_frames = self.bs.receive(data)
        messages = [self.mp.parse(bf) for bf in binary_frames]
        return messages


class HeaderByteStream:

    def __init__(self, header_length):
        self.buf = b''
        self.reading_header = True
        self.payload_length = None
        self.header_length = header_length

    def receive(self, b):
        """Collect complete binary frames from incoming byte stream.

        Args:
            b (bytes): Some bytes from the wire.

        Returns:
            list of byte arrays, each of which represents a complete frame.
        """
        self.buf = self.buf + b
        byte_frames= []

        while 1:
            if not self.reading_header and len(self.buf) >= self.payload_length:
                byte_frames.append(self.buf[0:self.payload_length])
                self.buf = self.buf[self.payload_length:]
                self.reading_header = True

            elif self.reading_header and len(self.buf) >= self.header_length:
                self.payload_length = int.from_bytes(
                    self.buf[0:self.header_length], 'big')
                self.buf = self.buf[self.header_length:]
                self.reading_header = False
            else:
                break
        return byte_frames



class JSONParser:
    def parse(self, data):
        return json.loads(data.decode('utf-8'))

