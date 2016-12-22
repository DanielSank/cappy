import cappy.pool as pool
import cappy.stream as stream


class Protocol:

    def __init__(self, writer, future_factory, implementation_class):
        self.stream = stream.Stream(
                stream.HeaderByteStream(2),
                stream.JSONParser())
        self.id_pool = pool.MessageIdPool()
        self.pending_requests = {}  # (int) --> Future
        self._writer = writer
        self.future_factory = future_factory

        self.implementation = implementation_class(self.make_outbound_request)

    def is_inbound_request(self, message):
        return message['id'] > 0

    def is_response(self, message):
        return message['id'] < 0

    def data_received(self, data):
        return self.stream.receive(data)

    def make_outbound_request(self, message):
        message_id = self.id_pool.get_id()
        message['id'] = message_id
        print("Making outbound request on method {} with "
              "args {} and id {}".format(
                  message['method'], message['args'], message['id']))
        self.write(self.stream.pack_message(message))
        f = self.future_factory()
        self.pending_requests[message_id] = f
        return f

    def handle_response(self, message):
        result = message['result']
        message_id = message['id']
        print('handling response to message {} with result {}'.format(
            message_id, result))
        self.pending_requests[-message_id].set_result(result)
        self.id_pool.return_id(-message_id)
        del self.pending_requests[-message_id]

    def write(self, data):
        self._writer(data)

