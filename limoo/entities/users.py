class Users:

    def __init__(self, driver):
        self._driver = driver

    _GET_USER = 'user/items/{}'
    async def get(self, user_id='self'):
        return await self._driver.execute_api_get(self._GET_USER.format(user_id))
