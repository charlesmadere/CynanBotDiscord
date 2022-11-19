import json
import os
from typing import Dict

import CynanBotCommon.utils as utils


class AuthRepository():

    def __init__(
        self,
        authFile: str = 'authFile.json'
    ):
        if not utils.isValidStr(authFile):
            raise ValueError(f'argument is malformed: \"{authFile}\"')

        self.__authFile: str = authFile

    def requireDiscordToken(self) -> str:
        jsonContents = self.__readJson()

        discordToken = jsonContents.get('discordToken')
        if not utils.isValidStr(discordToken):
            raise ValueError(f'\"discordToken\" in auth file \"{self.__authFile}\" is malformed: \"{discordToken}\"')

        return discordToken

    def requireTwitchClientId(self) -> str:
        jsonContents = self.__readJson()

        twitchClientId = jsonContents.get('twitchClientId')
        if not utils.isValidStr(twitchClientId):
            raise ValueError(f'\"twitchClientId\" in auth file \"{self.__authFile}\" is malformed: \"{twitchClientId}\"')

        return twitchClientId

    def requireTwitchClientSecret(self) -> str:
        jsonContents = self.__readJson()

        twitchClientSecret = jsonContents.get('twitchClientSecret')
        if not utils.isValidStr(twitchClientSecret):
            raise ValueError(f'\"twitchClientSecret\" in auth file \"{self.__authFile}\" is malformed: \"{twitchClientSecret}\"')

        return twitchClientSecret

    def __readJson(self) -> Dict[str, object]:
        if not os.path.exists(self.__authFile):
            raise FileNotFoundError(f'Auth file not found: \"{self.__authFile}\"')

        with open(self.__authFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from auth file: \"{self.__authFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of auth file \"{self.__authFile}\" is empty')

        return jsonContents
