import json
import os
from typing import List

import CynanBotCommon.utils as utils


class TwitchAnnounceServer():

    def __init__(
        self,
        discordChannelId: int,
        discordUserIds: List[int]
    ):
        if not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')
        elif not utils.hasItems(discordUserIds):
            raise ValueError(f'discordUserIds argument is malformed: \"{discordUserIds}\"')

        self.__discordChannelId = discordChannelId
        self.__discordUserIds = discordUserIds

    def getDiscordChannelId(self) -> int:
        return self.__discordChannelId

    def getDiscordUserIds(self) -> List[int]:
        return self.__discordUserIds


class TwitchAnnounceUser():

    def __init__(
        self,
        discordDiscriminator: int,
        discordId: int,
        discordName: str,
        twitchName: str
    ):
        if not utils.isValidNum(discordDiscriminator):
            raise ValueError(f'discordDiscriminator argument is malformed: \"{discordDiscriminator}\"')
        elif not utils.isValidNum(discordId):
            raise ValueError(f'discordId argument is malformed: \"{discordId}\"')
        elif not utils.isValidStr(discordName):
            raise ValueError(f'discordName argument is malformed: \"{discordName}\"')
        elif not utils.isValidStr(twitchName):
            raise ValueError(f'twitchName argument is malformed: \"{twitchName}\"')

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

    def getTwitchName(self) -> str:
        return self.__twitchName

    def toJsonDict(self) -> dict:
        return {
            'discordDiscriminator': self.__discordDiscriminator,
            'discordId': self.__discordId,
            'discordName': self.__discordName,
            'twitchName': self.__twitchName
        }


class TwitchAnnounceSettingsHelper():

    def __init__(
        self,
        twitchAnnounceSettingsFile: str = 'twitchAnnounceSettings.json'
    ):
        if not utils.isValidStr(twitchAnnounceSettingsFile):
            raise ValueError(f'twitchAnnounceSettingsFile argument is malformed: \"{twitchAnnounceSettingsFile}\"')

        self.__twitchAnnounceSettingsFile = twitchAnnounceSettingsFile

    def addUserToTwitchAnnounceUsers(
        self,
        discordDiscriminator: int,
        discordId: int,
        discordName: str,
        twitchName: str
    ) -> TwitchAnnounceUser:
        if not utils.isValidNum(discordDiscriminator):
            raise ValueError(f'discordDiscriminator argument is malformed: \"{discordDiscriminator}\"')
        elif not utils.isValidNum(discordId):
            raise ValueError(f'discordId argument is malformed: \"{discordId}\"')
        elif not utils.isValidStr(discordName):
            raise ValueError(f'discordName argument is malformed: \"{discordName}\"')
        elif not utils.isValidStr(twitchName):
            raise ValueError(f'twitchName argument is malformed: \"{twitchName}\"')

        jsonContents = self.__readJson()
        add = True

        user = TwitchAnnounceUser(
            discordDiscriminator = discordDiscriminator,
            discordId = discordId,
            discordName = discordName,
            twitchName = twitchName
        )

        for userJson in jsonContents['twitchAnnounceUsers']:
            if utils.getIntFromDict(userJson, 'discordId') == user.getDiscordId():
                userJson['discordDiscriminator'] = user.getDiscordDiscriminator()
                userJson['discordName'] = user.getDiscordName()
                userJson['twitchName'] = user.getTwitchName()
                add = False

        if add:
            jsonContents['twitchAnnounceUsers'].append(user.toJsonDict())

        jsonContents['twitchAnnounceUsers'].sort(key = lambda x: x['twitchName'].lower())

        with open(self.__twitchAnnounceSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent = 4, sort_keys = True)

        return user

    def getAllTwitchAnnounceUsers(self) -> List[TwitchAnnounceUser]:
        jsonContents = self.__readJson()

        twitchAnnounceUsersJson = jsonContents['twitchAnnounceUsers']
        if not utils.hasItems(twitchAnnounceUsersJson):
            return None

        twitchAnnounceUsers = list()

        for userJson in twitchAnnounceUsersJson:
            twitchAnnounceUsers.append(TwitchAnnounceUser(
                discordId = utils.getIntFromDict(userJson, 'discordId'),
                discordDiscriminator = utils.getIntFromDict(userJson, 'discordDiscriminator'),
                discordName = userJson['discordName'],
                twitchName = userJson['twitchName']
            ))

        return twitchAnnounceUsers

    def getRefreshEverySeconds(self) -> int:
        jsonContents = self.__readJson()
        refreshEverySeconds = utils.getIntFromDict(jsonContents, 'refreshEverySeconds')

        if refreshEverySeconds < 300:
            raise ValueError(f'\"refreshEverySeconds\" is too aggressive: {refreshEverySeconds}')

        return refreshEverySeconds

    def getTwitchAnnounceServersForUser(self, discordUserId: int) -> List[TwitchAnnounceUser]:
        if not utils.isValidNum(discordUserId):
            raise ValueError(f'discordUserId argument is malformed: \"{discordUserId}\"')

        jsonContents = self.__readJson()
        serversJson = jsonContents.get('twitchAnnounceServers')

        if not utils.hasItems(serversJson):
            raise RuntimeError(f'The \"twitchAnnounceServers\" field is either empty or missing in \"{self.__twitchAnnounceSettingsFile}\"')

        twitchAnnounceServers = list()

        for serverJson in serversJson:
            discordUserIds = serverJson['discordUserIds']

            if discordUserId in discordUserIds:
                twitchAnnounceServers.append(TwitchAnnounceServer(
                    discordChannelId = utils.getIntFromDict(serverJson, 'discordChannelId'),
                    discordUserIds = discordUserIds
                ))

        if not utils.hasItems(twitchAnnounceServers):
            print(f'Unable to find any TwitchAnnounceServer for discord user ID \"{discordUserId}\" in \"{self.__twitchAnnounceSettingsFile}\"')

        return twitchAnnounceServers

    def __readJson(self) -> dict:
        if not os.path.exists(self.__twitchAnnounceSettingsFile):
            raise FileNotFoundError(f'Twitch announce settings file not found: \"{self.__twitchAnnounceSettingsFile}\"')

        with open(self.__twitchAnnounceSettingsFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Twitch announce settings file: \"{self.__twitchAnnounceSettingsFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Twitch announce settings file \"{self.__twitchAnnounceSettingsFile}\" is empty')

        return jsonContents

    def removeUserFromTwitchAnnounceUsers(self, discordId: int) -> TwitchAnnounceUser:
        if not utils.isValidNum(discordId):
            raise ValueError(f'discordId argument is malformed: \"{discordId}\"')

        jsonContents = self.__readJson()
        user = None

        for userJson in jsonContents['twitchAnnounceUsers']:
            userDiscordId = utils.getIntFromDict(userJson, 'discordId')

            if userDiscordId == discordId:
                user = TwitchAnnounceUser(
                    discordDiscriminator = utils.getIntFromDict(userJson, 'discordDiscriminator'),
                    discordId = userDiscordId,
                    discordName = userJson['discordName'],
                    twitchName = userJson['twitchName']
                )

                jsonContents['twitchAnnounceUsers'].remove(userJson)
                break

        with open(self.__twitchAnnounceSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent = 4, sort_keys = True)

        return user
