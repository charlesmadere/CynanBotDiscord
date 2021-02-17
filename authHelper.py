import json
import os

import CynanBotCommon.utils as utils


class AuthHelper():

    def __init__(
        self,
        authFile: str = 'authFile.json'
    ):
        if not utils.isValidStr(authFile):
            raise ValueError(f'argument is malformed: \"{authFile}\"')

        self.__authFile = authFile

        if not os.path.exists(authFile):
            raise FileNotFoundError(f'Auth file not found: \"{authFile}\"')

        with open(authFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from auth file: \"{authFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of auth file \"{authFile}\" is empty')

        discordToken = jsonContents.get('discordToken')
        if not utils.isValidStr(discordToken):
            raise ValueError(f'Auth file \"{authFile}\" has malformed \"discordToken\" value: \"{discordToken}\"')
        self.__discordToken = discordToken

        twitchClientId = jsonContents.get('twitchClientId')
        if not utils.isValidStr(twitchClientId):
            raise ValueError(f'Auth file \"{authFile}\" has malformed \"twitchClientId\" value: \"{twitchClientId}\"')
        self.__twitchClientId = twitchClientId

    def getDiscordToken(self) -> str:
        return self.__discordToken

    def getTwitchClientId(self) -> str:
        return self.__twitchClientId
