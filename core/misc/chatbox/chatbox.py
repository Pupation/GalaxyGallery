from . import chatbox_router
from main import gg
import aioredis as redis
import json
import asyncio

from fastapi import WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from typing import List
import datetime

from models.user.auth import current_user, Permission
from models.misc.message import MessageHandler, Message

from utils.cache import redis_connection_pool
from utils.connection.nosql.db import client as nosql_client

NAME_MESSAGE_QUEUE = 'GG_NEWMESSAGE_QUEUE'
CACHED_PUBLIC_CHAT = []

CHAT_LOCK = asyncio.Lock()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_json(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except RuntimeError:
                self.active_connections.remove(connection)


manager = ConnectionManager()

async def register_websocket_sub():
    # while True:
    print('subscriber lanuched')
    client = redis.StrictRedis(connection_pool=redis_connection_pool)
    channel = client.pubsub()
    await channel.subscribe(NAME_MESSAGE_QUEUE)
    async for message in channel.listen():
        if message is None:
            continue
        # for message in channel.listen():
        print(message)
        if message['type'] == 'subscribe':
            continue
        if message['data'] == b'KILL':
            print("Redis subscriber exited!")
            break
        data = json.loads(message['data'])
        if data['receiver_uid'] == -1:
            await append_message(data)
            asyncio.create_task(manager.broadcast_json(data))

@gg.on_event('startup')
def launch_thread():
    print('---------try luanching')
    # t = threading.Thread(target=register_websocket_sub)
    # t.start()
    asyncio.create_task(register_websocket_sub())
    import signal
    
@gg.get('/kill')
async def kill():
    client = redis.StrictRedis(connection_pool=redis_connection_pool)
    client.publish(NAME_MESSAGE_QUEUE, 'KILL')

html = html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/chatbox/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiYWRtaW4iLCJ1aWQiOjEsImV4cCI6MTY2NjQwMDIyMn0.B43L8FRJNgcQMpnsykOe_ULD9ZznHCTzyLFHGv63hSA");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(JSON.stringify({ sender_uid: 1, receiver_uid: -1, content: input.value, send_time: Date.now(), quote: 0 }))
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

@chatbox_router.get('/testpage')
async def test_page():
    return HTMLResponse(html)

async def insert_public_chat():
    global CHAT_LOCK
    await CHAT_LOCK.acquire()

    


async def get_public_chat():
    global CACHED_PUBLIC_CHAT, CHAT_LOCK
    if not CHAT_LOCK.locked():
        await CHAT_LOCK.acquire()
        if len(CACHED_PUBLIC_CHAT) < 30:
            print("fetch database")
            CACHED_PUBLIC_CHAT = []
            for message in await nosql_client.messages.find({'receiver_uid': -1}).sort('send_time', -1).limit(30).to_list(30):
                d = Message(**dict(message))
                CACHED_PUBLIC_CHAT.append(json.loads(d.json()))
        CHAT_LOCK.release()
        return CACHED_PUBLIC_CHAT
    else:
        while CHAT_LOCK.locked():
            await asyncio.sleep(0.05)
        return CACHED_PUBLIC_CHAT

async def append_message(message):
    global CACHED_PUBLIC_CHAT, CHAT_LOCK
    await CHAT_LOCK.acquire()
    CACHED_PUBLIC_CHAT.insert(0, message)
    while len(CACHED_PUBLIC_CHAT) > 30:
        CACHED_PUBLIC_CHAT.pop()
    CHAT_LOCK.release()


@chatbox_router.websocket("/chatbox/ws") # FIXME: Upstream has a bug here dealing with prefix
async def chatebox_websocket(websocket: WebSocket, token: str = ''):
    global CACHED_PUBLIC_CHAT
    user = await current_user(token)
    await manager.connect(websocket)
    public_chat = await get_public_chat()

    await websocket.send_json(public_chat)
    while True:
        try:
            data = await websocket.receive_json()
        except:
            break
        if not user.has_permission(Permission.CHAT):
            await websocket.close()
            break
        try:
            message = MessageHandler(**data)
            message.message.send_time = datetime.datetime.now()
        except:
            websocket.send_json({'error': 422, 'detail': 'Validation failed.'})
            continue
        message.sender_uid = user.id
        client = redis.StrictRedis(connection_pool=redis_connection_pool)
        await client.publish(NAME_MESSAGE_QUEUE, message.message.json())
        await nosql_client.messages.insert_one(message.message.dict())
        await websocket.send_text(f"Message was {data}")