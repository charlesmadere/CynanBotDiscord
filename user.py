from typing import Optional

import CynanBotCommon.utils as utils
from CynanBotCommon.simpleDateTime import SimpleDateTime
from CynanBotCommon.users.userInterface import UserInterface


class User(UserInterface):

    def __init__(
        self,
        discordDiscriminator: str,
        discordId: str,
        discordName: str,
        mostRecentStreamDateTime: Optional[SimpleDateTime] = None,
        twitchName: Optional[str] = None
    ):
        if not utils.isValidStr(discordDiscriminator):
            raise ValueError(f'discordDiscriminator argument is malformed: \"{discordDiscriminator}\"')
        elif not utils.isValidStr(discordId):
            raise ValueError(f'discordId argument is malformed: \"{discordId}\"')
        elif not utils.isValidStr(discordName):
            raise ValueError(f'discordName argument is malformed: \"{discordName}\"')

        self.__discordDiscriminator: str = discordDiscriminator
        self.__discordId: str = discordId
        self.__discordName: str = discordName
        self.__mostRecentStreamDateTime: Optional[SimpleDateTime] = mostRecentStreamDateTime
        self.__twitchName: Optional[str] = twitchName

    def getDiscordDiscriminator(self) -> str:
        return self.__discordDiscriminator

    def getDiscordId(self) -> str:
        return self.__discordId

    def getDiscordName(self) -> str:
        return self.__discordName

    def getDiscordNameAndDiscriminator(self) -> str:
        return f'{self.__discordName}#{self.__discordDiscriminator}'

    def getHandle(self) -> str:
        return self.getDiscordName()

    def getMostRecentStreamDateTime(self) -> Optional[SimpleDateTime]:
        return self.__mostRecentStreamDateTime

    def getTwitchName(self) -> Optional[str]:
        return self.__twitchName

    def hasMostRecentStreamDateTime(self) -> bool:
        return self.__mostRecentStreamDateTime is not None

    def hasTwitchName(self) -> bool:
        return utils.isValidStr(self.__twitchName)

    def setMostRecentStreamDateTime(self, mostRecentStreamDateTime: Optional[SimpleDateTime]):
        self.__mostRecentStreamDateTime = mostRecentStreamDateTime
