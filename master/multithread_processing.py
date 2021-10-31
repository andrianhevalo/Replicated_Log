from concurrent.futures import ThreadPoolExecutor
import os
import requests


def multi_thread_processing(message):
    """
    :param message:
    :return:
    """
    endpoints = [os.getenv('secondary_a_path', 'http://localhost:5001') + '/messages',
                 os.getenv('secondary_b_path', 'http://localhost:5002') + '/messages']

    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            executor.map(lambda endpoint: requests.post(endpoint, json=message), endpoints)
        except:
            return "Message failed to be added to secondaries"

    return "Messages have been successfully added to secondaries"


