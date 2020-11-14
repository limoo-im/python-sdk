class Files:

    def __init__(self, driver):
        self._driver = driver

    async def upload(self, file, name, mime_type):
        name = str(name)
        if not name:
            raise ValueError('name should not be an empty string.')
        mime_type = str(mime_type)
        if not mime_type:
            raise ValueError('mime_type should not be an empty string.')
        return await self._driver._upload_file(file, name, mime_type)

    async def download(self, hash, name):
        hash = str(hash)
        if not hash:
            raise ValueError('hash should not be an empty string.')
        name = str(name)
        if not name:
            raise ValueError('name should not be an empty string.')
        return await self._driver._download_file(hash, name)
