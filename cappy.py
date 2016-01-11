"""
protocol

REQUEST
  jsonrpc (string): "2.0"
  method (string): name of method to call
  params *(struct): parameter values for method call
  id *(string, number, or NULL): if omitted, is notification

RESPONSE
  jsonrps (string): "2.0"
  result: Do not include if error.
  error (object):
  id (string, number): 
"""

import json


class Future(object):
    pass


class DataStream(object):
    """Consumes bytes and produces JSON objects"""

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
                if self.buf != '':
                    completed = self.buf + data[start_index: i+1]

                objects.append(json.loads(completed))
                # The loads call here produces a python dict with an arbitrary
                # number of fields, etc. In a statically typed language we'd
                # prefer the loads equivalent to produce a more structured
                # result. In particular, we probably can't do _all_ of the
                # unflattening in one step.

                start_index = i+1
                self.buf = ''
        self.buf += data[start_index:]
        return objects


class Protocol(object):

    def __init__(self, stream):
        self.stream = stream

    def data_received(self, data):
        messages = self.stream.receive(data)
        if len(messages) > 0:
            for message in messages:
                self.handle_message(message)

    def handle_message(message):
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
        method = message['method']
        # We use the 'method' field of JSONRPC as the target object identifier.

        request_id = message['id']

        if method == "remote object call":
            self.handle_inbound_capability(message['params'], request_id)
        raise Exception("method {} not recognized".format(
            method))

    def handle_inbound_capability(params, request_id):
        """

        Args:
            params (dict: str -> str): Parameter name -> stringified value.
        """
        capability_id = params['target']  # Int
        method_name = params['method name']  # String
        params = params['params']  # map: string -> Any in a typed language

        try:
            capability = self.capabilities[capability_id]  # Capability
        except KeyError as e:
            print("No object with id {} exists".format(object_id))
            raise

        result = capability.handle_remote_method_invocation(method_name,
                capability.parsers[method_name](params))

        self.handle_outbound_response(request_id, result)


class Capability(object):
    def handle_remote_method_invocation(method_name, params):
        pass

    
