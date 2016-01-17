import cappy
import pytest

class TestJsonDataStrem(object):

    def test_single_object(self):
        stream = cappy.JsonDataStream()
        result = stream.receive("""{"id": 1, "name": "Daniel"}""")
        assert result == [{'id': 1, 'name': "Daniel"}]

    def test_multiple_objects(self):
        stream = cappy.JsonDataStream()
        result = stream.receive("""{"id":1, "name": "Daniel"}{"id": 2}""")
        assert result == [{'id': 1, 'name': "Daniel"}, {'id': 2}]

    def test_partial_streams(self):
        messages = """{"id": 1, "name": "Daniel"}{"color": "green"}"""
        stream = cappy.JsonDataStream()
        result = stream.receive(messages[0:10])
        assert result == []
        result = stream.receive(messages[10:])
        assert result == [{'id': 1, 'name': "Daniel"},{'color': "green"}]
