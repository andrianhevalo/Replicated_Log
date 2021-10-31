from flask import Flask, request
from multithread_processing import multi_thread_processing

message_list = []
app = Flask(__name__)


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
    multi_thread_processing(message)

    message_list.append(message["message"])

    return "Message added successfully", 201


@app.route('/messages', methods=['GET'])
def return_messages():
    """
    :return:
    """
    global message_list

    return message_list


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
