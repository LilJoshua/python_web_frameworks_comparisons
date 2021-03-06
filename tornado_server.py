#!/usr/bin/env python

import asyncio

import uvloop
from tornado.platform.asyncio import AsyncIOMainLoop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
AsyncIOMainLoop().install()

import aiohttp
import os
import tornado.httpserver
from tornado.httpclient import AsyncHTTPClient
import tornado.ioloop
import tornado.web
import ujson as json
from tornado.options import options

options.define('port', default=8080, type=int, help="Server port")
GO_SLEEP_ADDRESS = os.getenv('GO_SLEEP_ADDRESS', '127.0.0.1:8090')

_connector = aiohttp.TCPConnector(ttl_dns_cache=300, limit=10000, keepalive_timeout=30)


class JsonHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def write_response(self, data):
        self.write(json.dumps(data))


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


class SingleQueryHandler(JsonHandler):
    async def get(self):
        seconds = 3
        url = f'http://{GO_SLEEP_ADDRESS}/?seconds={seconds}'
        async with aiohttp.ClientSession(connector=_connector, connector_owner=False) as session:
            body = await fetch(session, url)
        self.write(body)


class MultipleQueriesHandler(JsonHandler):
    async def get(self):
        client = AsyncHTTPClient()
        seconds = 1.5
        url = f'http://{GO_SLEEP_ADDRESS}/?seconds={seconds}'

        body_list = []

        url = f'http://192.168.10.18:8090/?seconds={seconds}'
        async with aiohttp.ClientSession(connector=_connector, connector_owner=False) as session:
            body = await fetch(session, url)
        body_list.append(body)
        url = f'http://192.168.10.18:8090/?seconds={seconds}'
        async with aiohttp.ClientSession(connector=_connector, connector_owner=False) as session:
            body = await fetch(session, url)
        body_list.append(body)

        self.write('\n'.join(body_list))


def make_app():
    return tornado.web.Application([
        (r"/single", SingleQueryHandler),
        (r"/multiple", MultipleQueriesHandler),
    ],
        template_path="templates"
    )


app = make_app()

if __name__ == "__main__":
    options.parse_command_line()

    server = tornado.httpserver.HTTPServer(app)
    server.bind(options.port)
    server.start(1)

    asyncio.get_event_loop().run_forever()
