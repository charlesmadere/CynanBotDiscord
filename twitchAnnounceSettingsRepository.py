import json
import os
from typing import Any, Dict, Optional

import aiofiles
import aiofiles.ospath

import CynanBotCommon.utils as utils
from twitchAnnounceSettingsSnapshot import TwitchAnnounceSettingsSnapshot


class TwitchAnnounceSettingsRepository():

    def __init__(
        self,
        twitchAnnounceSettingsFile: str = 'twitchAnnounceSettings.json'
    ):
        if not utils.isValidStr(twitchAnnounceSettingsFile):
            raise ValueError(f'twitchAnnounceSettingsFile argument is malformed: \"{twitchAnnounceSettingsFile}\"')

        self.__twitchAnnounceSettingsFile: str = twitchAnnounceSettingsFile
        self.__cache: Optional[TwitchAnnounceSettingsSnapshot] = None

    def getAll(self) -> TwitchAnnounceSettingsSnapshot:
        if self.__cache is not None:
            return self.__cache

        jsonContents = self.__readJson()
        snapshot = TwitchAnnounceSettingsSnapshot(jsonContents, self.__twitchAnnounceSettingsFile)
        self.__cache = snapshot

        return snapshot

    async def getAllAsync(self) -> TwitchAnnounceSettingsSnapshot:
        if self.__cache is not None:
            return self.__cache

        jsonContents = await self.__readJsonAsync()
        snapshot = TwitchAnnounceSettingsSnapshot(jsonContents, self.__twitchAnnounceSettingsFile)
        self.__cache = snapshot

        return snapshot

    def __readJson(self) -> Dict[str, Any]:
        if not os.path.exists(self.__twitchAnnounceSettingsFile):
            raise FileNotFoundError(f'Twitch announce settings file not found: \"{self.__twitchAnnounceSettingsFile}\"')

        with open(self.__twitchAnnounceSettingsFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Twitch announce settings file: \"{self.__twitchAnnounceSettingsFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Twitch announce settings file \"{self.__twitchAnnounceSettingsFile}\" is empty')

        return jsonContents

    async def __readJsonAsync(self) -> Dict[str, Any]:
        if not await aiofiles.ospath.exists(self.__twitchAnnounceSettingsFile):
            raise FileNotFoundError(f'Twitch announce settings file not found: \"{self.__twitchAnnounceSettingsFile}\"')

        async with aiofiles.open(self.__twitchAnnounceSettingsFile, mode = 'r') as file:
            data = await file.read()
            jsonContents = json.loads(data)

        if jsonContents is None:
            raise IOError(f'Error reading from Twitch announce settings file: \"{self.__twitchAnnounceSettingsFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Twitch announce settings file \"{self.__twitchAnnounceSettingsFile}\" is empty')

        return jsonContents
