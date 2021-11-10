from main import config, gg
import aio_pika
from aio_pika.pool import Pool
from asyncio import get_running_loop, create_task
from datetime import datetime, timedelta
from typing import Union
import pickle

async def _get_connection():
    return await aio_pika.connect_robust(config.db.mq)

connection_pool = Pool(_get_connection, max_size=4, loop=get_running_loop())


async def _get_channel() -> aio_pika.Channel:
    global connection_pool
    async with connection_pool.acquire() as connection:
        return await connection.channel()

channel_pool = Pool(_get_channel, max_size=40, loop=get_running_loop())


@gg.on_event('startup')
async def initialize_delayed_mq():
    channel = await _get_channel()
    exchange = await channel.declare_exchange('delayed', 'x-delayed-message', True, False, arguments={'x-delayed-type': 'direct'})
    create_task(consume_dealyed_message())


async def consume_dealyed_message():
    channel: aio_pika.Channel
    async with channel_pool.acquire() as channel:
        from .delay import delay
        await channel.set_qos(10)
        exchange = await channel.get_exchange('delayed')
        queue = await channel.declare_queue('delayed_queue')
        await queue.bind(exchange, '')
        async with queue.iterator() as iter:
            async for message in iter:
                async with message.process():
                    # print(message.body)
                    await delay.execute(pickle.loads(message.body))


async def publish_with_delay(message, delay: Union[timedelta, datetime] = timedelta(seconds=5)):
    channel: aio_pika.Channel
    if isinstance(delay, datetime):
        delay = delay - datetime.now()
    delay:int = int(delay.total_seconds() * 1000)
    async with channel_pool.acquire() as channel:
        exchange = await channel.get_exchange('delayed')
        # exchange = channel.default_exchange
        msg = aio_pika.Message(body=pickle.dumps(message),
            headers={
                'x-delay': delay
            }
        )
        await exchange.publish(msg, '')
    
from .delay import delay