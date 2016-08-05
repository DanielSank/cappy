import stream
import pytest


class TestJsonDataStrem(object):

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

