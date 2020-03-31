# Limoo Python SDK
A Python SDK for Limoo.  
  
*Wondering what Limoo is? Visit https://limoo.im*  
  
*Give Limoo a try: https://web.limoo.im*

### Dependencies
aiohttp >= 3.6

### Example usage
```python
# Create a new LimooDriver instance given limoo server, bot username and bot password
async with LimooDriver('https://web.limoo.im/Limonad', 'test_bot_username', 'test_bot_password') as ld:
    # find the id of the user we're logged in as
    my_info = await ld.request(LimooDriver.Method.GET, 'user/items/self')
    print(my_info['id'])
    
    # A listener which is notified whenever a new message is sent in any conversation of the workspace
    async def listener(ld, event):
        print(event['data']['message']['text'])

        # Send a message in the thread of the new message (msg can be root of a thread only if its threadRootId is null)
	if not event['data']['message']['thread_root_id']:
	    body = {
                'text': 'Got your message.',
		'thread_root_id': event['data']['message']['thread_root_id'],
            }
            await ld.send(event['data']['message']['conversation_id'], body)

    # Register the listener
    ld.add_listener(listener)

    # Start listening
    ld.start_listening()

    # Sleep for a five minutes
    await asyncio.sleep(300)
```

### Bot creation
In order to create a bot, send the following command in your direct conversation with Limoo Bot:

<div dir="rtl">

```
/ساخت-بات my_bot bot_nickname
```

</div>

Note that only admins of the workspace can create bots.
