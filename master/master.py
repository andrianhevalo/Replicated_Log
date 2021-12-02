import os
import asyncio
import uvicorn
from fastapi import FastAPI
import requests_async as requests
import json
from node_health import NodeHealth
from message import Message


class Node:
    def __init__(self, path, endpoint, health_endpoint, health: NodeHealth):
        self.path, self.endpoint, self.health_endpoint, self.health = path, endpoint, health_endpoint, health


paths = [os.getenv('secondary_a_path', 'http://secondary_a:5001'),
         os.getenv('secondary_b_path', 'http://secondary_b:5002')]


endpoints = [os.getenv('secondary_a_path', 'http://secondary_a:5001') + '/messages',
             os.getenv('secondary_b_path', 'http://secondary_b:5002') + '/messages']


health_endpoints = [os.getenv('secondary_a_path', 'http://secondary_a:5001') + '/status',
                    os.getenv('secondary_b_path', 'http://secondary_b:5002') + '/status']


nodes = {}  # {'path': Node}

message_list = []
available_message_list: [Message] = []

MinDelay = 0.1
MaxDelay = 5
HealthCheckDelay = 1

app = FastAPI()

# API def:
@app.route('/')
def empty():
    return "Hello from master!"


@app.get('/status')
async def welcome():
    await initial_setup()
    return "OK!"


@app.get('/messages/list')
def get():
    print(_quorum_exists())
    return {"data": json.dumps(available_message_list)}


@app.post('/messages/new')
async def append_message(message, w: int):
    print(f'_quorum_exists() {_quorum_exists()}')
    if _quorum_exists():
        result = await _replicate(message, w)
        return result[1]
    else:
        return 'No quorum, master can not write messages'


# Replication
async def _replicate(text, w) -> (bool, str):
    if w == 0:
        return False, 'Write concern must be > 0'
    else:
        id = len(message_list)
        message: Message = Message(id=id, text=text)
        message_list.append(message)
        message_to_send = message.create_json()
        tasks = []

        w = w - 1
        if w > len(paths):
            w = len(paths)
        for endpoint in paths:
            task = asyncio.create_task(_post_to_endpoint_retrying(endpoint, message_to_send))
            tasks.append(task)

        tasks_list = list(tasks)

        if w == 0:
            _append_to_available_list(message)
            asyncio.gather(*tasks_list)
            return True, 'Message was successfully saved'

        for cor in asyncio.as_completed(tasks_list):
            result = await cor
            if result[0]:
                w -= 1
                print(f'result = {result}, w = {w}')
            if w <= 0:
                print(f'w = {w}')
                _append_to_available_list(Message.create_from(result[1]))
                return True, 'Message was successfully saved'
        return False, 'Failed to save a message'

def _append_to_available_list(message) -> (bool, NodeHealth):
    if not available_message_list.__contains__(message):
        available_message_list.append(message)


# Lost messages replication:
def _unsent_messages_for(message_json) -> [Message]:
    message: Message = Message.create_from(message_json)
    id = message.id
    print(f'id = {id}')
    print(f'current available {available_message_list}')
    filtered = list(filter(lambda cur: cur.id >= id, available_message_list))
    print(f'filtered messages {filtered}')
    return filtered

# Retry:
async def _post_to_endpoint_retrying(endpoint, data) -> (bool, json):
    data_to_send = [data]
    success = False
    n = -1
    node = nodes[endpoint]
    while not success:
        try:
            n += 1
            delay = _delay_for_retry(n)
            time = asyncio.get_running_loop().time()
            print(f'using delay {delay} sec, current time {time}')
            waited = await asyncio.sleep(delay, result=True, loop=asyncio.get_running_loop())
            if waited:
                #check node healthiness
                node = nodes[endpoint]
                is_healthy = node.health
                print(f'healthiness_status {is_healthy}')
                if is_healthy != NodeHealth.HEALTHY:
                    print(f'node {endpoint} seems to be failed, not retrying')
                    continue
                time = asyncio.get_running_loop().time()
                print(f'trying for the {n} time, current time {time}')
                if n > 0:
                    print('n > 0')
                    unsent = _unsent_messages_for(data)
                    print(f'unsent messages {unsent}')
                    data_to_send = unsent
                print(f'sending data {data_to_send}')
                result = await requests.post(node.endpoint, json=data_to_send)
        except:
            print('Concern-replication exception')
            continue
        if result.status_code == 201:
            success = True
        else:
            success = False
    print(f'returning with {success}')
    return success, data

def _delay_for_retry(n) -> float:
    if n <= 0:
        return 0
    return min(pow(n, 2) * 0.1, MaxDelay)


# Health checking:
async def initial_setup():
    for path in paths:
        node = Node(path, path + '/messages', path + '/status', NodeHealth.HEALTHY)
        nodes[path] = node
    await start_health_checking()


async def start_health_checking():
    while True:
        time = asyncio.get_running_loop().time()
        print(f'waiting for health checking, time {time}')
        awaited = await asyncio.sleep(HealthCheckDelay, result=True)
        if awaited:
            time = asyncio.get_running_loop().time()
            print(f'health checking started at {time}')
            await _check_system_health()


async def _check_system_health():
    global nodes

    tasks = []
    for endpoint in paths:
        task = asyncio.create_task(_check_node_health(endpoint))
        tasks.append(task)
    tasks_list = list(tasks)

    for cor in asyncio.as_completed(tasks_list):
        result, endpoint = await cor
        node = nodes[endpoint]
        current_health: NodeHealth = node.health
        print(f'updating system health with result {result} for endpoint {endpoint}')
        if not result:
            update_node_health(endpoint, current_health.next())
        else:
            update_node_health(endpoint, NodeHealth.HEALTHY)


async def _check_node_health(endpoint) -> (bool, str):
    node = nodes[endpoint]
    try:
        result = await requests.get(node.health_endpoint)
    except:
        return False, endpoint
    return result.status_code == 200, endpoint

def update_node_health(path, health):
    node = nodes[path]
    node.health = health
    nodes[path] = node


# Quorum:
def _quorum_exists():
    number = int(len(list(paths)) / 2)
    healthy = filter(lambda node: node.health == NodeHealth.HEALTHY, nodes.values())
    current_quorum = len(list(healthy))
    print(f'Current quorum {current_quorum}')
    return current_quorum >= number


# Prev
async def _post_to_endpoint(endpoint, data) -> (bool, json):
    node = nodes[endpoint]
    try:
        result = await requests.post(node.endpoint, json=data)
    except:
        print('Concern-replication exception')
        return False, data
    if result.status_code == 201:
        return True, data
    else:
        return False, data

if __name__ == '__main__':
    uvicorn.run('master:app', host='0.0.0.0', port=5000, reload=True)
