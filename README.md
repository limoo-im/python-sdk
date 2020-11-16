# Limoo Python SDK
A Python SDK for Limoo.  
  
*Wondering what Limoo is? Visit https://limoo.im*  
  
*Give Limoo a try: https://web.limoo.im*

## Install

```
pip install limoo-sdk
```

## Example

The following is a simple echo bot. It listens to every conversation that it is
a member of and will reply to every message that it receives in that
conversation by echoing it back. It also echoes back the attached files by first
storing them locally and then uploading them to the server again.

```python
import asyncio
import contextlib
import json

from limoo import LimooDriver

async def respond(event):
    # We have to make sure that the created message was not created by us.
    if (event['event'] == 'message_created'
        and event['data']['message']['user_id'] != self['id']):
        attached_files = list()
        for file_data in event['data']['message']['files'] or list():
            sr = await ld.files.download(file_data['hash'], file_data['name'])
            with open(f'download/{file_data["name"]}', 'wb') as file:
                data = await sr.read()
                while data:
                    file.write(data)
                    data = await sr.read()
            with open(f'download/{file_data["name"]}', 'rb') as file:
                # Uploading a file requires a name and a MIME type. We can
                # reuse the information from the attached files of the received
                # message.
                file_info = await ld.files.upload(file, file_data['name'], file_data['mime_type'])
                attached_files.append(file_info[0])
        message_id = event['data']['message']['id']
        thread_root_id = event['data']['message']['thread_root_id']
        direct_reply_message_id = event['data']['message']['thread_root_id'] and event['data']['message']['id']
        # If the received message is part of a thread, it will have
        # thread_root_id set and we need to reuse that thread_root_id so that
        # our message ends up in the same thread. We also set
        # direct_reply_message_id to the id of the message so our message is
        # sent as a reply to the received message. If however, the received
        # message does not have thread_root_id set, we will create a new thread
        # by setting thread_root_id to the id of the received message. In this
        # case, we must set direct_reply_message_id to None.
        response = await ld.messages.create(
	    event['data']['workspace_id'],
	    event['data']['message']['conversation_id'],
	    event['data']['message']['text'],
	    thread_root_id=thread_root_id or message_id,
	    direct_reply_message_id=thread_root_id and message_id,
	    files=attached_files)

async def listen(ld):
    forever = asyncio.get_running_loop().create_future()
    # The given event_handler will be called on the event loop thread for each
    # event received from the WebSocket. Also it must be a normal function and
    # not a coroutine therefore we create our own task so that our coroutine
    # gets executed.
    ld.set_event_handler(lambda event: asyncio.create_task(respond(event)))
    await forever

async def main():
    global ld, self
    async with contextlib.AsyncExitStack() as stack:
        ld = LimooDriver('web.limoo.im', 'botusername', 'botpassword')
        stack.push_async_callback(ld.close)
        # Calling ld.users.get without any arguments gets information
        # about the currently logged in user
        self = await ld.users.get()
        await listen(ld)

asyncio.run(main())
```

## API

### Limoo API

The current version of the Limoo API is available at
https://web.limoo.im/Limonad/api_reference/index.html which maps out the
structure of the WebSocket events and the objects received from the methods in
this SDK.

### SDK

Right now the API is not yet stable so you should probably thoroughly test your
code to make sure it still works with newer versions. Also we don't yet have
a proper documentation but try and stick with what is documented in this file as
everything else will probably not be part of the API.

## Requirements

Python >= 3.7

[aiohttp](https://github.com/aio-libs/aiohttp) ~= 3.7

## Bot creation
In order to create a bot, send the following command in your direct conversation with Limoo Bot:

<div dir="rtl">

```
/ساخت-بات my_bot bot_nickname
```

</div>

Note that only admins of the workspace can create bots.
