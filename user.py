import CynanBotCommon.utils as utils

class User():

    def __init__(
        self,
        discordDiscriminator: int,
        discordId: int,
        discordName: str,
        twitchName: str = None
    ):
        if not utils.isValidNum(discordDiscriminator):
            raise ValueError(f'discordDiscriminator argument is malformed: \"{discordDiscriminator}\"')
        elif not utils.isValidNum(discordId):
            raise ValueError(f'discordId argument is malformed: \"{discordId}\"')
        elif not utils.isValidStr(discordName):
            raise ValueError(f'discordName argument is malformed: \"{discordName}\"')

        self.__discordDiscriminator = discordDiscriminator
        self.__discordId = discordId
        self.__discordName = discordName
        self.__twitchName = twitchName

    def getDiscordDiscriminator(self) -> int:
        return self.__discordDiscriminator

    def getDiscordId(self) -> int:
        return self.__discordId

    def getDiscordName(self) -> str:
        return self.__discordName

    def getDiscordNameAndDiscriminator(self) -> str:
        return f'{self.__discordName}#{self.__discordDiscriminator}'

    def getTwitchName(self) -> str:
        return self.__twitchName

    def hasTwitchName(self) -> bool:
        return self.__twitchName