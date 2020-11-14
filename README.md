# Limoo Python SDK
A Python SDK for Limoo.  
  
*Wondering what Limoo is? Visit https://limoo.im*  
  
*Give Limoo a try: https://web.limoo.im*

### Dependencies
aiohttp >= 3.7

### Example usage
```python
import asyncio
import contextlib
import json

from limoo import LimooDriver

async def respond(event):
    if event['event'] == 'message_created' and event['data']['message']['user_id'] != self['id']:
        attached_files = list()
        for file_data in event['data']['message']['files'] or list():
            sr = await ld.files.download(file_data['hash'], file_data['name'])
            with open(f'download/{file_data["name"]}', 'wb') as file:
                data = await sr.read()
                while data:
                    file.write(data)
                    data = await sr.read()
            with open(f'download/{file_data["name"]}', 'rb') as file:
                file_info = await ld.files.upload(file, file_data['name'], file_data['mime_type'])
                file_info[0]['mime_type'] = file_info[0].pop('contentType')
                attached_files.append(file_info[0])
        message_id = event['data']['message']['id']
        thread_root_id = event['data']['message']['thread_root_id']
        direct_reply_message_id = event['data']['message']['thread_root_id'] and event['data']['message']['id']
        response = await ld.messages.create(event['data']['workspace_id'], event['data']['message']['conversation_id'], event['data']['message']['text'], thread_root_id=thread_root_id or message_id, direct_reply_message_id=thread_root_id and message_id, files=attached_files)

async def listen(ld):
    forever = asyncio.get_running_loop().create_future()
    ld.set_event_handler(lambda event: asyncio.create_task(respond(event)))
    await forever

async def main():
    global ld, self
    async with contextlib.AsyncExitStack() as stack:
        ld = LimooDriver('web.limoo.im', 'botusername', 'botpassword')
        stack.push_async_callback(ld.close)
        self = await ld.users.get()
        await listen(ld)

asyncio.run(main())
```

### Bot creation
In order to create a bot, send the following command in your direct conversation with Limoo Bot:

<div dir="rtl">

```
/ساخت-بات my_bot bot_nickname
```

</div>

Note that only admins of the workspace can create bots.
