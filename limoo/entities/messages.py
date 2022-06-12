from ..exceptions import LimooError


class Messages:

    def __init__(self, driver):
        self._driver = driver

    _CREATE = 'workspace/items/{}/conversation/items/{}/message/items'
    async def create(self, workspace_id, conversation_id, text, *, thread_root_id=None, direct_reply_message_id=None, files=None, message_type=None):
        body = {'text': text}
        if thread_root_id:
            body['thread_root_id'] = thread_root_id
        if direct_reply_message_id:
            body['direct_reply_message_id'] = direct_reply_message_id
        if files:
            body['files'] = files
        if message_type:
            body['type'] = message_type
        return await self._driver._execute_api_post(self._CREATE.format(workspace_id, conversation_id), body=body)

    _SEND = 'workspace/items/{}/message/items'
    async def send(self, workspace_id, receiver_phone_number, text, *, thread_root_id=None, direct_reply_message_id=None, files=None):
        body = {'receiver_phone_number': receiver_phone_number, 'text': text}
        if thread_root_id:
            body['thread_root_id'] = thread_root_id
        if direct_reply_message_id:
            body['direct_reply_message_id'] = direct_reply_message_id
        if files:
            body['files'] = files
        return await self._driver._execute_api_post(self._SEND.format(workspace_id), body=body)
