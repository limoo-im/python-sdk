class Files:

    def __init__(self, driver):
        self._driver = driver

    async def upload(self, path, name, mime_type):
        return await self._driver._upload_file(path, name, mime_type)

    async def download(self, hash, name):
        return await self._driver._download_file(hash, name)
