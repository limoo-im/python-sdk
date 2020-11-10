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

from limoo import LimooDriver

async def respond(event):
    # We only care about message creation events that are not caused by us
    if event['event'] == 'message_created' and event['data']['message']['user_id'] != self['id']:
        # Send a message to say we received the last message
        await ld.messages.create(event['data']['workspace_id'], event['data']['message']['conversation_id'], 'got your message')

async def listen(ld):
    forever = asyncio.get_running_loop().create_future()
    # A WebSocket to receive events sent by the server
    ld.start_websocket(lambda event: asyncio.create_task(respond(event)))
    await forever

async def main():
    global ld, self
    async with contextlib.AsyncExitStack() as stack:
        # Create a new LimooDriver instance given limoo server, bot username and bot password
        ld = LimooDriver('web.limoo.im', 'bot_username', 'bot_password')
        stack.push_async_callback(ld.close)
	# Find information about the user we're logged in as
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
