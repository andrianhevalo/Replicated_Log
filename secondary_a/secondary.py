from flask import Flask, request
import time
import os

app = Flask(__name__)

message_list = []
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
    global message_list
    message = request.get_json()
    time.sleep(int(delay))
    message_list.append(message)
    return "New message successfully added to secondary", 201


@app.route('/messages', methods=['GET'])
def return_messages():
    """
    :return:
    """
    global message_list
    return {"data": message_list}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

