import os
import asyncio
import uvicorn
from fastapi import FastAPI
import requests_async as requests
import json

endpoints = [os.getenv('secondary_a_path', 'http://secondary_a:5001') + '/messages',
             os.getenv('secondary_b_path', 'http://secondary_b:5002') + '/messages']

message_list = []
available_message_list = []

app = FastAPI()


@app.route('/')
def empty():
    return "Hello from master!"


@app.get('/status')
def welcome():
    return "OK!"


@app.get('/messages/list')
def get():
    return {"data": available_message_list}


@app.post('/messages/new')
async def append_message(message, w: int):
    result = await _replicate(message, w)
    return result[1]


async def _post_to_endpoint(endpoint, data) -> (bool, json):
    try:
        result = await requests.post(endpoint, json=data)
    except:
        print('Concern-replication exception')
        return False, data
    if result.status_code == 201:
        return True, data
    else:
        return False, data


async def _replicate(message, w) -> (bool, str):
    if w == 0:
        return False, 'Write concern must be > 0'
    else:
        id = len(message_list)
        message_to_send = json.dumps({'id': id, 'text': message})
        message_list.append(message_to_send)
        tasks = []

        w = w - 1
        if w > len(endpoints):
            w = len(endpoints)

        for endpoint in endpoints:
            task = asyncio.create_task(_post_to_endpoint(endpoint, message_to_send))
            tasks.append(task)

        tasks_list = list(tasks)

        if w == 0:
            _append_to_available_list(message_to_send)
            asyncio.gather(*tasks_list)
            return True, 'Message was successfully saved'

        for cor in asyncio.as_completed(tasks_list):
            result = await cor
            if result[0]:
                w -= 1
                print(f'result = {result}, w = {w}')
            if w <= 0:
                print(f'w = {w}')
                _append_to_available_list(result[1])
                return True, 'Message was successfully saved'
        return False, 'Failed to save a message'


def _append_to_available_list(message):
    if not available_message_list.__contains__(message):
        available_message_list.append(message)


if __name__ == '__main__':
    uvicorn.run('master:app', host='0.0.0.0', port=5000, reload=True)
