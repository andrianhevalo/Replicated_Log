from collections import namedtuple
from json import JSONEncoder
import json

class Message:
    def __init__(self, id, text):
        self.id, self.text = id, text

    def create_json(self):
        return json.dumps(self, cls=MessageEncoder)

    @staticmethod
    def create_from(json_obj):
        return json.loads(json_obj, object_hook=message_decoder)


class MessageEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def message_decoder(dict):
    return namedtuple('Message', dict.keys())(*dict.values())
