from ..exceptions import LimooError


class Messages:

    def __init__(self, driver):
        self._driver = driver

    _CREATE = 'workspace/items/{}/conversation/items/{}/message/items'
    async def create(self, workspace_id, conversation_id, text, *, thread_root_id=None, direct_reply_message_id=None):
        workspace_id = str(workspace_id)
        if not workspace_id:
            raise ValueError('workspace_id should not be an empty string.')
        conversation_id = str(conversation_id)
        if not conversation_id:
            raise ValueError('conversation_id should not be an empty string.')
        body = {'text': str(text)}
        if thread_root_id is not None:
            thread_root_id = str(thread_root_id)
            if not thread_root_id:
                raise ValueError('thread_root_id should not be an emtpy string.')
            body['thread_root_id'] = thread_root_id
        if direct_reply_message_id is not None:
            direct_reply_message_id = str(direct_reply_message_id)
            if not direct_reply_message_id:
                raise ValueError('direct_reply_message_id should not be an empty string.')
            body['direct_reply_message_id'] = direct_reply_message_id
        if 'direct_reply_message_id' in body:
            if 'thread_root_id' not in body:
                raise LimooError('direct_reply_message_id can only be set when thread_root_id is also set.')
            if body['direct_reply_message_id'] == body['thread_root_id']:
                raise LimooError('direct_reply_message_id cannot be equal to thread_root_id.')
        return await self._driver._execute_api_post(self._CREATE.format(workspace_id, conversation_id), body=body)
