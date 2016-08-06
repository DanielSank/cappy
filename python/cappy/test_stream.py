import cappy.stream as stream
import pytest


class TestHeaderByteStream:

    def test_single_frame(self):
        s = stream.HeaderByteStream(2)
        data = b'\x00\x03ABC'
        result = s.receive(data)
        assert result == [b'ABC']

    def test_multiple_frames(self):
        s = stream.HeaderByteStream(2)
        result = s.receive(b'\x00\x02AB\x00\x041234')
        assert result == [b'AB', b'1234']

    def test_partial_frames(self):
        s = stream.HeaderByteStream(2)
        data = b'\x00\x03ABC\x00\x0212'
        result = s.receive(data[0:4])
        assert result == []
        result = s.receive(data[4:7])
        assert result == [b'ABC']
        result = s.receive(data[7:])
        assert result == [b'12']


class TestJSONDataStrem:

    def test_single_object(self):
        s = stream.Stream(stream.HeaderByteStream(2), stream.JSONParser())
        result = s.receive(
            b'\x00\x1b{"id": 1, "name": "Daniel"}')
        assert result == [{'id': 1, 'name': "Daniel"}]

    def test_multiple_objects(self):
        s = stream.Stream(stream.HeaderByteStream(2), stream.JSONParser())
        result = s.receive(
            b'\x00\x1b{"id": 1, "name": "Daniel"}\x00\x09{"id": 2}')
        assert result == [{'id': 1, 'name': "Daniel"}, {'id': 2}]

    def test_partial_streams(self):
        s = stream.Stream(stream.HeaderByteStream(2), stream.JSONParser())
        data = b'\x00\x1b{"id": 1, "name": "Daniel"}\x00\x12{"color": "green"}'
        result = s.receive(data[0:10])
        assert result == []
        result = s.receive(data[10:])
        assert result == [{'id': 1, 'name': "Daniel"},{'color': "green"}]

