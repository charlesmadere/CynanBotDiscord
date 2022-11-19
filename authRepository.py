import json
import os
from typing import Any, Dict, Optional

import aiofiles
import aiofiles.ospath

import CynanBotCommon.utils as utils
from authSnapshot import AuthSnapshot


class AuthRepository():

    def __init__(
        self,
        authFile: str = 'authFile.json'
    ):
        if not utils.isValidStr(authFile):
            raise ValueError(f'argument is malformed: \"{authFile}\"')

        self.__authFile: str = authFile
        self.__cache: Optional[AuthSnapshot] = None

    async def clearCaches(self):
        self.__cache = None

    def getAll(self) -> AuthSnapshot:
        if self.__cache is not None:
            return self.__cache

        jsonContents = self.__readJson()
        snapshot = AuthSnapshot(jsonContents, self.__authFile)
        self.__cache = snapshot

        return snapshot

    async def getAllAsync(self) -> AuthSnapshot:
        if self.__cache is not None:
            return self.__cache

        jsonContents = await self.__readJsonAsync()
        snapshot = AuthSnapshot(jsonContents, self.__authFile)
        self.__cache = snapshot

        return snapshot

    def __readJson(self) -> Dict[str, Any]:
        if not os.path.exists(self.__authFile):
            raise FileNotFoundError(f'Auth file not found: \"{self.__authFile}\"')

        with open(self.__authFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from auth file: \"{self.__authFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of auth file \"{self.__authFile}\" is empty')

        return jsonContents

    async def __readJsonAsync(self) -> Dict[str, Any]:
        if not await aiofiles.ospath.exists(self.__authFile):
            raise FileNotFoundError(f'Auth file not found: \"{self.__authFile}\"')

        async with aiofiles.open(self.__authFile, mode = 'r') as file:
            data = await file.read()
            jsonContents = json.loads(data)

        if jsonContents is None:
            raise IOError(f'Error reading from auth file: \"{self.__authFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of auth file \"{self.__authFile}\" is empty')

        return jsonContents
