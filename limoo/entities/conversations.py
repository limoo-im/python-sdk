class Conversations:

    def __init__(self, driver):
        self._driver = driver

    _CREATE = 'workspace/items/{}/conversation/items'
    async def create(self, workspace_id, *, user_ids):
        workspace_id = str(workspace_id)
        if not workspace_id:
            raise ValueError('workspace_id should not be an empty string.')
        user_id_list = list()
        for count, user_id in enumerate(user_ids, start=1):
            if count > 2:
                raise ValueError('user_ids must be an iterable of exactly two user IDs.')
            user_id = str(user_id)
            if not user_id:
                raise ValueError('user_ids should be an iterable of non empty strings.')
            user_id_list.append(user_id)
        if len(user_id_list) < 2:
            raise ValueError('user_ids must be an iterable of exactly two user IDs.')
        body = {
            'user_ids': user_id_list,
            'type': 'direct',
        }
        return await self._driver._execute_api_post(self._CREATE.format(workspace_id), body=body)
