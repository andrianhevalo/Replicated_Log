from flask import Flask, request
import time

app = Flask(__name__)

message_list = []


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
    time.sleep(5)
    message_list.append(message["message"])
    return "New message successfully added to secondary", 201


@app.route('/messages', methods=['GET'])
def return_messages():
    """
    :return:
    """
    global message_list
    return message_list, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

