import urllib.parse


class Conversations:

    def __init__(self, driver):
        self._driver = driver

    _GET = 'workspace/items/{}/conversation/items/{}'
    async def get(self, workspace_id, conversation_id):
        endpoint = self._GET.format(workspace_id, conversation_id)
        return await self._driver._execute_api_get(endpoint)

    _CREATE = 'workspace/items/{}/conversation/items'
    async def create(self, workspace_id, *, user_ids=[], conversation_type='direct', display_name=None, icon_hash=None):
        body = {
            'user_ids': user_ids,
            'type': conversation_type,
        }
        if display_name:
            body["display_name"] = display_name
        
        if icon_hash:
            body["icon_hash"] = icon_hash
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

    _ADDـMEMBERS = "workspace/items/{}/conversation/items/{}/members/batch"
    async def add_members(self, workspace_id, conversation_id, users):
        endpoint = self._ADDـMEMBERS.format(workspace_id, conversation_id)
        body = users
        return await self._driver._execute_api_post(endpoint, body=body)

    _ARCHIVE = "workspace/items/{}/conversation/items/{}/archive"
    async def archive(self, workspace_id, conversation_id):
        body = {}
        endpoint = self._ARCHIVE.format(workspace_id, conversation_id)
        return await self._driver._execute_api_post(endpoint, body=body)
    
    _UNARCHIVE = "workspace/items/{}/conversation/items/{}/unarchive"
    async def unarchive(self, workspace_id, conversation_id):
        body = {}
        endpoint = self._UNARCHIVE.format(workspace_id, conversation_id)
        return await self._driver._execute_api_post(endpoint, body=body)

    _CHANGE_ROLES = "workspace/items/{}/conversation/items/{}/members/items/{}/roles"
    async def change_member_roles(self, workspace_id, conversation_id, user_id, roles):
        body = roles
        endpoint = self._CHANGE_ROLES.format(workspace_id, conversation_id, user_id)
        return await self._driver._execute_api_post(endpoint, body=body)



