from ..exceptions import LimooError


class Messages:

    def __init__(self, driver):
        self._driver = driver

    _CREATE = 'workspace/items/{}/conversation/items/{}/message/items'
    async def create(self, workspace_id, conversation_id, text, *, thread_root_id=None, direct_reply_message_id=None, files=None):
        body = {'text': text}
        if thread_root_id:
            body['thread_root_id'] = thread_root_id
        if direct_reply_message_id:
            body['direct_reply_message_id'] = direct_reply_message_id
        if files:
            body['files'] = files
        return await self._driver._execute_api_post(self._CREATE.format(workspace_id, conversation_id), body=body)
