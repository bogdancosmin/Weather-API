import asyncio
import aioredis
from weather import data

async def connect_tcp():
    conn = await aioredis.create_connection(
        ('localhost', 6379))
    val = await conn.execute('GET', 'data')


asyncio.get_event_loop().run_until_complete(connect_tcp())