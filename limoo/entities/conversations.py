import urllib.parse


class Conversations:

    def __init__(self, driver):
        self._driver = driver

    _CREATE = 'workspace/items/{}/conversation/items'
    async def create(self, workspace_id, *, user_ids):
        body = {
            'user_ids': user_ids,
            'type': 'direct',
        }
        return await self._driver._execute_api_post(self._CREATE.format(workspace_id), body=body)

    _PUBLICS = 'workspace/items/{}/conversation/public'
    async def publics(self, workspace_id, *, query=None, include_archived=None):
        endpoint = self._PUBLICS.format(workspace_id)
        params = dict()
        if query is not None:
            params['query'] = query
        if include_archived is not None:
            params['include_archived'] = include_archived
        if params:
            endpoint = f'{endpoint}?{urllib.parse.urlencode(params)}'
        return await self._driver._execute_api_get(endpoint)

    _MINE = 'workspace/items/{}/conversation/items/'
    async def mine(self, workspace_id, *, include_archived=None):
        endpoint = self._MINE.format(workspace_id)
        params = dict()
        if include_archived is not None:
            params['include_archived'] = include_archived
        if params:
            endpoint = f'{endpoint}?{urllib.parse.urlencode(params)}'
        return await self._driver._execute_api_get(endpoint)
