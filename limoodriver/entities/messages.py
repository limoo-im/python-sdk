class Messages:

    def __init__(self, driver):
        self._driver = driver

    _CREATE = 'workspace/items/{}/conversation/items/{}/message/items'
    async def create(self, workspace_id, conversation_id, text):
        return await self._driver.execute_api_post(self._CREATE.format(workspace_id, conversation_id), body={'text': text})
