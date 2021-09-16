#!env/bin/python

from time import sleep

from aiohttp.client_exceptions import ServerDisconnectedError

import asyncio
import aiohttp

from aioeagle import EagleHub
from prometheus_client import start_http_server, Summary, Gauge, Enum, Counter

import config

REQUEST_TIME = Summary(
    'request_processing_seconds',
    'Time spent processing request'
)
connected = Enum(
    'meter_connected',
    'Connection state to meter',
    states=['connected', 'disconnected']
)

demand = Gauge('instantaneous_demand', 'Instantaneous Demand')
consumed = Counter('total_consumed', 'Current Consumed KWh to date')

@REQUEST_TIME.time()
async def process_request():
    async with aiohttp.ClientSession() as session:
        await run(session)

async def run(session):
    try:
        hub = EagleHub(
            session,
            config.CLOUD_ID,
            config.INSTALL_CODE,
            host=config.EAGLE_IP
        )

        devices = await hub.get_device_list()
        metrics = await devices[0].get_device_query()

        connected.state('connected' if devices[0].is_connected else 'disconnected')
        demand.set(metrics['zigbee:InstantaneousDemand']['Value'])
        consumed.set(metrics['zigbee:CurrentSummationDelivered']['Value'])
    except ServerDisconnectedError as e:
        print(e)


if __name__ == '__main__':
    start_http_server(8888)
    while True:
        asyncio.run(process_request())
        sleep(30)
