import asyncio
import contextlib
import functools
import json
import logging
import urllib.parse

from aiohttp import ClientConnectionError, ClientPayloadError, ClientSession, CookieJar, FormData

from .entities import Conversations, Files, Messages, Users, Workspaces
from .exceptions import LimooAuthenticationError, LimooError

_LOGGER = logging.getLogger('limoo')


class StreamReader:

    def __init__(self, response):
        self._response = response

    async def read(self):
        try:
            return await self._response.content.readany()
        except (ClientConnectionError, ClientPayloadError) as ex:
            await self._response.release()
            raise LimooError from ex


class LimooDriver:

    _ALLOWED_CONNECTION_ATTEMPTS = 1000000
    _RETRY_DELAY = 2

    @staticmethod
    async def _receive_event(ws):
        while True:
            try:
                return await ws.receive_json()
            except ValueError:
                continue

    @staticmethod
    async def _get_text_body(response):
        try:
            return await response.text()
        except (ClientConnectionError, ClientPayloadError) as ex:
            raise LimooError from ex
        finally:
            await response.release()

    @staticmethod
    async def _get_json_body(response):
        response_text = await LimooDriver._get_text_body(response)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as ex:
            raise LimooError('Response body is not valid json: {resonse_text}') from ex

    def _with_auth(coro):
        @functools.wraps(coro)
        async def wrapper(self, *args, **kwargs):
            async with self._authlock:
                authenticated = False
                previous_slc = self._successful_login_count
            while True:
                try:
                    return await coro(self, *args, **kwargs)
                except LimooAuthenticationError:
                    if authenticated:
                        raise
                    async with self._authlock:
                        if self._successful_login_count == previous_slc:
                            await self._login()
                            self._successful_login_count += 1
                            authenticated = True
                        previous_slc = self._successful_login_count
        return wrapper

    def __init__(self, limoo_url, bot_username, bot_password, secure=True):
        self._credentials = {
            'j_username': bot_username,
	    'j_password': bot_password,
        }
        if limoo_url.endswith('/'):
            limoo_url = limoo_url[:-1]
        http_url = f'http{"s" if secure else ""}://{limoo_url}'
        ws_url = f'ws{"s" if secure else ""}://{limoo_url}'
        self._login_url = f'{http_url}/Limonad/j_spring_security_check'
        self._api_url_prefix = f'{http_url}/Limonad/api/v1'
        self._fileop_url = f'{http_url}/fileserver/api/v1/files'
        self._websocket_url = f'{ws_url}/Limonad/websocket'
        self._client_session = ClientSession(cookie_jar=CookieJar(unsafe=True))
        self._successful_login_count = 0
        self._authlock = asyncio.Lock()
        self._listen_task = None
        self._event_handler = lambda event: None
        self.conversations = Conversations(self)
        self.files = Files(self)
        self.messages = Messages(self)
        self.users = Users(self)
        self.workspaces = Workspaces(self)

    async def close(self):
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        await self._client_session.close()

    async def _login(self):
        await self._execute_request('POST', self._login_url, data=self._credentials)

    @_with_auth
    async def _execute_api_get(self, endpoint):
        return await self._execute_json_request('GET', endpoint)

    @_with_auth
    async def _execute_api_post(self, endpoint, body):
        return await self._execute_json_request('POST', endpoint, body=body)

    async def _execute_json_request(self, method, endpoint, *, body=None):
        return await self._get_json_body(await self._execute_request(method, f'{self._api_url_prefix}/{endpoint}', json=body))

    @_with_auth
    async def _upload_file(self, path, name, mime_type):
        formdata = FormData(quote_fields=False)
        run_async = asyncio.get_running_loop().run_in_executor
        async with contextlib.AsyncExitStack() as stack:
            file = await run_async(None, open, path, 'rb')
            stack.push_async_callback(run_async, None, file.close)
            formdata.add_field(name, file, content_type=mime_type, filename=name)
            return await self._get_json_body(await self._execute_request('POST', self._fileop_url, data=formdata))

    @_with_auth
    async def _download_file(self, hash, name):
        params = urllib.parse.urlencode({'hash': hash, 'name': name})
        return StreamReader(await self._execute_request('GET', f'{self._fileop_url}?mode=download&{params}'))

    async def _execute_request(self, method, url, *, data=None, json=None):
        try:
            response = await self._client_session.request(method, url, data=data, json=json)
        except ClientConnectionError as ex:
            raise LimooError('Connection Error') from ex
        status = response.status
        if status < 400:
            return response
        response_text = await self._get_text_body(response)
        if status == 401:
            raise LimooAuthenticationError
        else:
            raise LimooError(f'Request returned unsuccessfully with status {status} and body {response_text}')

    def set_event_handler(self, event_handler):
        if event_handler is not None and not callable(event_handler):
            raise ValueError('event_handler must either be a callable or None.')
        self._event_handler = event_handler
        if self._event_handler and not self._listen_task:
            self._listen_task = asyncio.create_task(self._listen())
        elif not self._event_handler and self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None

    async def _listen(self):
        _LOGGER.info('WebSocket listen task started.')
        cancel_ex = None
        max_delay = self._ALLOWED_CONNECTION_ATTEMPTS * (self._RETRY_DELAY + 1)
        while not cancel_ex:
            ws = None
            for retry_delay in range(self._RETRY_DELAY, max_delay + self._RETRY_DELAY, self._RETRY_DELAY):
                try:
                    ws = await self._try_connecting()
                    break
                except asyncio.CancelledError as ex:
                    cancel_ex = ex
                    break
                except Exception as ex:
                    _LOGGER.error('Connecting the WebSocket failed with the following exception: %s',  ex)
                    if retry_delay == max_delay:
                        break
                    else:
                        _LOGGER.info('Going to sleep for %d seconds before trying to connect a WebSocket.', retry_delay)
                        try:
                            await asyncio.sleep(retry_delay)
                        except asyncio.CancelledError as ex:
                            cancel_ex = ex
                            break
            if not ws:
                break
            _LOGGER.info('Connected the WebSocket.')
            while True:
                try:
                    event = await self._receive_event(ws)
                except asyncio.CancelledError as ex:
                    cancel_ex = ex
                    break
                except Exception as ex:
                    _LOGGER.error('The connected WebSocket broke with the following exception: %s', ex)
                    break
                _LOGGER.debug('Received an event.')
                try:
                    self._event_handler(event)
                except Exception as ex:
                    _LOGGER.error('Calling the event handler failed with the following exception: %s', ex)
            try:
                await ws.close()
                _LOGGER.info('The WebSocket was closed.')
            except asyncio.CancelledError as ex:
                cancel_ex = ex
            except Exception as ex:
                _LOGGER.error('Closing the WebSocket failed with the following exception: %s', ex)
        _LOGGER.info('WebSocket listen task ended.')
        if cancel_ex:
            raise cancel_ex

    @_with_auth
    async def _try_connecting(self):
        async with contextlib.AsyncExitStack() as stack:
            ws = await stack.enter_async_context(self._client_session.ws_connect(self._websocket_url, receive_timeout=70, heartbeat=60))
            event = await self._receive_event(ws)
            if event.get('event') == 'authentication_failed':
                raise LimooAuthenticationError
            else:
                stack.pop_all()
                return ws

    del _with_auth
