from datetime import datetime

import CynanBotCommon.utils as utils


class User():

    def __init__(
        self,
        discordDiscriminator: str,
        discordId: str,
        discordName: str,
        mostRecentStreamDateTime: datetime = None,
        twitchName: str = None
    ):
        if not utils.isValidStr(discordDiscriminator):
            raise ValueError(f'discordDiscriminator argument is malformed: \"{discordDiscriminator}\"')
        elif not utils.isValidStr(discordId):
            raise ValueError(f'discordId argument is malformed: \"{discordId}\"')
        elif not utils.isValidStr(discordName):
            raise ValueError(f'discordName argument is malformed: \"{discordName}\"')

        self.__discordDiscriminator = discordDiscriminator
        self.__discordId = discordId
        self.__discordName = discordName
        self.__mostRecentStreamDateTime = mostRecentStreamDateTime
        self.__twitchName = twitchName

    def getDiscordDiscriminator(self) -> str:
        return self.__discordDiscriminator

    def getDiscordId(self) -> str:
        return self.__discordId

    def getDiscordName(self) -> str:
        return self.__discordName

    def getDiscordNameAndDiscriminator(self) -> str:
        return f'{self.__discordName}#{self.__discordDiscriminator}'

    def getMostRecentStreamDateTime(self) -> datetime:
        return self.__mostRecentStreamDateTime

    def getMostRecentStreamDateTimeStr(self) -> str:
        return utils.getStrFromDateTime(self.__mostRecentStreamDateTime)

    def getTwitchName(self) -> str:
        return self.__twitchName

    def hasMostRecentStreamDateTime(self) -> bool:
        return self.__mostRecentStreamDateTime is not None

    def hasTwitchName(self) -> bool:
        return self.__twitchName

    def setMostRecentStreamDateTime(self, mostRecentStreamDateTime: datetime):
        self.__mostRecentStreamDateTime = mostRecentStreamDateTime
