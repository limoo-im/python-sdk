import asyncio
import contextlib
import enum
import inspect
import json
import urllib.parse

import aiohttp


class LimooError(Exception):
    pass


class WebSocketError(LimooError):
    pass


class AuthFailed(WebSocketError):

    def __init__(self, msg):
        self.msg = msg


class ServerClosed(WebSocketError):

    def __init__(self, code, reason):
        self.code = code
        self.reason = reason


class HTTPError(LimooError):

    def __init__(self, status, raw_body):
        self.status = status
        self.raw_body = raw_body


class JSONHTTPError(HTTPError):

    def __init__(self, status, raw_body):
        super().__init__(status, raw_body)
        self._json = None

    def json(self):
        if self._json is None:
            self._json = json.loads(self.raw_body)
        return self._json


class InvalidRequest(JSONHTTPError):
    pass


class NoAccessToken(JSONHTTPError):
    pass


class NotPermitted(JSONHTTPError):
    pass


class NotFound(JSONHTTPError):
    pass


class FeatureDisabled(LimooError):
    pass


class LimooDriver:


    class Method(enum.Enum):
        DELETE = 'DELETE'
        GET = 'GET'
        POST = 'POST'


    _KNOWN_ERRORS = {
        400: InvalidRequest,
        401: NoAccessToken,
        403: NotPermitted,
        404: NotFound,
        501: FeatureDisabled,
    }

    def __init__(self, host, username, password):
        host = str(host)
        username = str(username)
        password = str(password)
        parts = ['https', host, None, '', '', '']
        parts[2] = 'Limonad/j_spring_security_check'
        self._login_url = urllib.parse.urlunparse(parts)
        parts[2] = 'Limonad/j_spring_jwt_security_check'
        self._refresh_url = urllib.parse.urlunparse(parts)
        parts[2] = 'Limonad/api/v1'
        self._api_url = urllib.parse.urlunparse(parts)
        parts[0] = 'wss'
        parts[2] = 'Limonad/websocket'
        self._websocket_url = urllib.parse.urlunparse(parts)
        self._auth_payload = {
            'j_username': username,
            'j_password': password,
        }
        self._session = aiohttp.ClientSession()
        self._authlock = asyncio.Lock()
        self._successful_auth_count = 0
        self._login_needed = True
        self._listeners = list()
        self._listen_task = None

    @property
    def closed(self):
        return self._session.closed

    async def close(self):
        if self.closed:
            raise RuntimeError('Already closed.')
        self.listener = None
        await self._session.close()

    async def __aenter__(self):
        if self.closed:
            raise RuntimeError('Closed.')
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if not self.closed:
            await self.close()

    async def _raise_for_status(self, response):
        if response.status < 400:
            return
        try:
            error_class = self._KNOWN_ERRORS[response.status]
        except KeyError:
            error_class = HTTPError
        raise error_class(response.status, await response.read())

    async def _with_auth(self, coro_func, *args, **kwargs):
        async with self._authlock:
            if self._login_needed:
                await self._login()
                self._login_needed = False
                self._successful_auth_count += 1
                authenticated = True
            else:
                authenticated = False
            previous_sac = self._successful_auth_count
        while True:
            try:
                return await coro_func(*args, **kwargs)
            except (AuthFailed, NoAccessToken):
                if authenticated:
                    raise
            async with self._authlock:
                if self._successful_auth_count == previous_sac:
                    if not self._login_needed:
                        try:
                            await self._refresh()
                        except NoAccessToken:
                            self._login_needed = True
                    if self._login_needed:
                        await self._login()
                        self._login_needed = False
                    self._successful_auth_count += 1
                    authenticated = True
                previous_sac = self._successful_auth_count

    async def _login(self):
        if self.closed:
            raise RuntimeError('Closed.')
        async with self._session.request('POST', self._login_url,
                                         data=self._auth_payload) as response:
            await self._raise_for_status(response)
            self._my_id = (await response.json())['id']
        my_workspaces = await self._request(
            f'{self._api_url}/user/my_workspaces', LimooDriver.Method.GET)
        if len(my_workspaces) > 1:
            raise RuntimeError
        self._my_workspace_id = my_workspaces[0]['id']

    async def _refresh(self):
        if self.closed:
            raise RuntimeError('Closed.')
        await self._request(self._refresh_url, LimooDriver.Method.POST)

    async def send(self, conversation_id, body):
        return await self._with_auth(self._send, conversation_id, body=body)

    async def _send(self, conversation_id, body):
        endpoint = f'{self._api_url}/workspace/items/{self._my_workspace_id}\
/conversation/items/{conversation_id}/message/items'
        return await self._request(endpoint, LimooDriver.Method.POST, body=body)

    async def request(self, endpoint, method, *, params=None, body=None):
        if not isinstance(method, LimooDriver.Method):
            raise TypeError('The method argument must be a member of the \
LimooDriver.Method Enum.')
        endpoint = str(endpoint)
        fullendpoint = f'{self._api_url}/{endpoint}'
        return await self._with_auth(self._request, fullendpoint, method,
                                     params=params, body=body)

    async def _request(self, endpoint, method, *, params=None, body=None):
        if self.closed:
            raise RuntimeError('Closed.')
        async with self._session.request(method.value, endpoint,
                                         params=params, json=body) as response:
            await self._raise_for_status(response)
            return await response.json()

    def add_listener(self, listener):
        if not inspect.iscoroutinefunction(listener):
            raise TypeError('The listener argument must be a coroutine.')
        self._listeners.append(listener)

    def remove_listener(self, listener):
        self._listeners.remove(listener)

    def start_listening(self):
        if not self._listen_task:
            self._listen_task = asyncio.create_task(self._listen())

    def stop_listening(self):
        if self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None
            
    async def _listen(self):
        while True:
            ws = None
            retry_delay = 1
            while not ws:
                try:
                    ws, ws_context = await self._with_auth(self._connection)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    await asyncio.sleep(retry_delay)
                    if retry_delay < 256:
                        retry_delay *= 2
            try:
                async with ws_context:
                    while True:
                        event = await self._receive(ws)
                        self._fire(event)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass

    def _fire(self, event):
        for listener in self._listeners:
            asyncio.create_task(self._exec(listener(self, event)))

    async def _exec(self, coro):
        try:
            await coro
        except asyncio.CancelledError:
            raise
        except Exception:
            pass

    async def _connection(self):
        async with contextlib.AsyncExitStack() as stack:
            ws = await stack.enter_async_context(self._session.ws_connect(
                self._websocket_url, receive_timeout=70, heartbeat=60))
            event = await ws.receive_json()
            if event['event'] == 'hello':
                return ws, stack.pop_all()
            else:
                raise AuthFailed(event)

    async def _receive(self, ws):
        event = None
        while not event:
            msg = await ws.receive()
            if msg.type is aiohttp.WSMsgType.TEXT:
                try:
                    event = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                if (event['event'] != 'message_created'
                    or event['data']['message']['user_id'] == self._my_id):
                    event = None
            else:
                if msg.type is aiohttp.WSMsgType.CLOSE:
                    err = ServerClosed(msg.data, msg.extra)
                else:
                    err = WebSocketError()
                raise err
        return event['data']
