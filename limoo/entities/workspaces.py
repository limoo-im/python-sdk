import urllib.parse


class Workspaces:

    def __init__(self, driver):
        self._driver = driver

    _MINE = 'user/my_workspaces'
    async def mine(self):
        return await self._driver._execute_api_get(self._MINE)
