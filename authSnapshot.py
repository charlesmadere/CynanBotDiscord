from typing import Any, Dict

import CynanBotCommon.utils as utils


class AuthSnapshot():

    def __init__(
        self,
        jsonContents: Dict[str, Any],
        authFile: str
    ):
        if not utils.hasItems(jsonContents):
            raise ValueError(f'jsonContents argument is malformed: \"{jsonContents}\"')
        elif not utils.isValidStr(authFile):
            raise ValueError(f'authFile argument is malformed: \"{authFile}\"')

        self.__jsonContents: Dict[str, Any] = jsonContents
        self.__authFile: str = authFile

    def requireDiscordToken(self) -> str:
        discordToken = self.__jsonContents.get('discordToken')

        if not utils.isValidStr(discordToken):
            raise ValueError(f'\"discordToken\" in auth file \"{self.__authFile}\" is malformed: \"{discordToken}\"')

        return discordToken

    def requireTwitchClientId(self) -> str:
        twitchClientId = self.__jsonContents.get('twitchClientId')

        if not utils.isValidStr(twitchClientId):
            raise ValueError(f'\"twitchClientId\" in auth file \"{self.__authFile}\" is malformed: \"{twitchClientId}\"')

        return twitchClientId

    def requireTwitchClientSecret(self) -> str:
        twitchClientSecret = self.__jsonContents.get('twitchClientSecret')

        if not utils.isValidStr(twitchClientSecret):
            raise ValueError(f'\"twitchClientSecret\" in auth file \"{self.__authFile}\" is malformed: \"{twitchClientSecret}\"')

        return twitchClientSecret
