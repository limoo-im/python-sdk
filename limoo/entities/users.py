class Users:

    def __init__(self, driver):
        self._driver = driver

    _GET_USER = 'user/items/{}'
    async def get(self, user_id=None):
        if user_id is None:
            user_id = 'self'
        else:
            user_id = str(user_id)
            if not user_id:
                raise ValueError('user_id should not be an empty string.')
        return await self._driver._execute_api_get(self._GET_USER.format(user_id))
