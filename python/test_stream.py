import stream
import pytest


class TestByteStream:

    def test_single_frame(self):
        s = stream.ByteStream()
        data = b'\x00\x03ABC'
        result = s.receive(data)
        assert result == [b'ABC']

    def test_multiple_frames(self):
        s = stream.ByteStream()
        result = s.receive(b'\x00\x02AB\x00\x041234')
        assert result == [b'AB', b'1234']

    def test_partial_frames(self):
        s = stream.ByteStream()
        data = b'\x00\x03ABC\x00\x0212'
        result = s.receive(data[0:4])
        assert result == []
        result = s.receive(data[4:7])
        assert result == [b'ABC']
        result = s.receive(data[7:])
        assert result == [b'12']


class TestJsonDataStrem:

    def test_single_object(self):
        s = stream.JsonDataStream()
        result = s.receive("""{"id": 1, "name": "Daniel"}""")
        assert result == [{'id': 1, 'name': "Daniel"}]

    def test_multiple_objects(self):
        s = stream.JsonDataStream()
        result = s.receive("""{"id":1, "name": "Daniel"}{"id": 2}""")
        assert result == [{'id': 1, 'name': "Daniel"}, {'id': 2}]

    def test_partial_streams(self):
        messages = """{"id": 1, "name": "Daniel"}{"color": "green"}"""
        s = stream.JsonDataStream()
        result = s.receive(messages[0:10])
        assert result == []
        result = s.receive(messages[10:])
        assert result == [{'id': 1, 'name': "Daniel"},{'color': "green"}]

