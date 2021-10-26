from . import chatbox_router
from main import gg
import redis
import json
import asyncio

from fastapi import WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from typing import List
import threading

from models.user.auth import current_user, Permission
from models.misc.message import MessageHandler

from utils.cache import redis_connection_pool

NAME_MESSAGE_QUEUE = 'GG_NEWMESSAGE_QUEUE'

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
            await connection.send_json(message)

manager = ConnectionManager()

def register_websocket_sub():
    # while True:
    print('subscriber lanuched')
    client = redis.StrictRedis(connection_pool=redis_connection_pool)
    channel = client.pubsub()
    channel.subscribe(NAME_MESSAGE_QUEUE)
    for message in channel.listen():
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
            asyncio.run(manager.broadcast_json(data))

@gg.on_event('startup')
def launch_thread():
    print('---------try luanching')
    t = threading.Thread(target=register_websocket_sub)
    t.start()

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
                ws.send(JSON.stringify({ sender_uid: 1, receiver_uid: -1, content: input.value, send_time: "2012-04-23T18:25:43.511Z", quote: 0 }))
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

@chatbox_router.websocket("/chatbox/ws") # FIXME: Upstream has a bug here dealing with prefix
async def chatebox_websocket(websocket: WebSocket, token: str = ''):
    user = await current_user(token)
    if not user.has_permission(Permission.CHAT):
        await websocket.close()
        raise HTTPException("You do not have permission to join this channel.", 403)
    await manager.connect(websocket)
    while True:
        data = await websocket.receive_json()
        try:
            message = MessageHandler(**data)
        except:
            websocket.send_json({'error': 422, 'detail': 'Missing field.'})
        client = redis.StrictRedis(connection_pool=redis_connection_pool)
        client.publish(NAME_MESSAGE_QUEUE, message.message.json())
        await websocket.send_text(f"Message was {data}")