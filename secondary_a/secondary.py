from flask import Flask, request
from json import loads
import time
import os


class MessageContainer:
    """
    Container for keeping messages with deduplication and total ordering
    """

    def __init__(self):
        self.messages = list()

    def append(self, message):

        self.messages.append(message)

    def return_messages(self):
        ids = [_[0] for _ in self.messages]

        if len(self.messages) == 0:
            return []

        if len(self.messages) == max(ids):
            return self.messages
        for current_id in ids:
            next_id = current_id + 1
            if next_id not in ids:
                return [[item[0], item[1]] for item in self.messages if item[0] < next_id]

        return sorted(self.messages)


app = Flask(__name__)

msg_container = MessageContainer()

delay = os.getenv('DELAY', '10')


@app.route('/')
def empty():
    return "Hello from secondary!"


@app.route('/status')
def welcome():
    return "OK!"


@app.route('/messages', methods=['POST'])
def append_message():
    """

    :return:
    """

    message = request.get_json()
    time.sleep(int(delay))

    if message not in msg_container.messages:
        msg_container.append(message)

        return "New message successfully added to secondary", 201
    return "New message failed to be added to secondary"


@app.route('/messages', methods=['GET'])
def return_messages():
    """
    :return:
    """

    return msg_container.return_messages()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

