import os
import asyncio
import attr
import random
from collections import defaultdict

from aiohttp import ClientResponse
from aiohttp import web, client_exceptions
from aiorpcx import timeout_after, TaskTimeout, ignore_after


from electrum.util import log_exceptions, ignore_exceptions, UserFacingException
from electrum.logging import Logger
from electrum.invoices import PR_PAID, PR_EXPIRED


class NotaryServer(Logger):
    """
    public API:
    - notarize: reply with an invoice
    - status: reply with proof
    - websocket for status updates
    """

    def __init__(self, config, wallet, notary):
        Logger.__init__(self)
        self.config = config
        self.wallet = wallet
        self.notary = notary
        self.port = self.config.NOTARY_SERVER_PORT

    @ignore_exceptions
    @log_exceptions
    async def run(self):
        self.root = '/root'
        app = web.Application()
        app.add_routes([web.post('/api/get_proof', self.get_proof)])
        app.add_routes([web.post('/api/verify_proof', self.verify_proof)])
        app.add_routes([web.post('/api/add_request', self.add_request)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=self.port)#, ssl_context=self.config.get_ssl_context())
        await site.start()
        self.logger.info(f"notary server is listening on port {self.port}")

    async def add_request(self, request):
        params = await request.json()
        try:
            event_id = bytes.fromhex(params['event_id'])
            value_sats = int(params['value_sats'])
            nonce = bytes.fromhex(params['nonce'])
            upvoter_pubkey = bytes.fromhex(params.get('upvoter_pubkey', ''))
            upvoter_signature = bytes.fromhex(params.get('upvoter_signature', ''))
        except Exception as e:
            self.logger.info(f"{request}, {params}, {e}")
            raise web.HTTPUnsupportedMediaType()
        try:
            r = self.notary.add_request(event_id, value_sats, nonce, upvoter_pubkey=upvoter_pubkey, upvoter_signature=upvoter_signature)
        except UserFacingException as e:
            self.logger.info(f"{request}, {params}, {e}")
            return web.json_response({"error":"{str(e)}"})
        return web.json_response(r)

    async def get_proof(self, request):
        params = await request.json()
        try:
            rhash = params['rhash']
            proof = self.notary.get_proof(rhash)
            await self.notary.verify_proof(proof)
        except UserFacingException as e:
            return web.json_response({"error":str(e)})
        except Exception as e:
            self.logger.info(f"{request}, {params}, {e}")
            raise web.HTTPUnsupportedMediaType()
        return web.json_response(proof)

    async def verify_proof(self, request):
        params = await request.json()
        try:
            result = await self.notary.verify_proof(params)
        except UserFacingException as e:
            return web.json_response({"error":str(e)})
        #except Exception as e:
        #    self.logger.info(f"{request}, {params}, {e}")
        #    raise web.HTTPUnsupportedMediaType()
        return web.json_response(result)
