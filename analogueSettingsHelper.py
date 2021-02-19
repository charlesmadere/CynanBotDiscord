import json
import os
from typing import Iterable, List

import CynanBotCommon.utils as utils
from CynanBotCommon.analogueStoreRepository import AnalogueProductType
from user import User


class AnalogueSettingsHelper():

    def __init__(
        self,
        analogueSettingsFile: str = 'analogueSettings.json'
    ):
        if not utils.isValidStr(analogueSettingsFile):
            raise ValueError(f'analogueSettingsFile argument is malformed: \"{analogueSettingsFile}\"')

        self.__analogueSettingsFile = analogueSettingsFile

    def addUser(self, user: User):
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')

        jsonContents = self.__readJson()
        add = True

        for userJson in jsonContents['usersToNotify']:
            if utils.getIntFromDict(userJson, 'id') == user.getDiscordId():
                userJson['discriminator'] = user.getDiscordDiscriminator()
                userJson['name'] = user.getDiscordName()
                add = False

        if add:
            jsonContents['usersToNotify'].append(self.__userToJson(user))

        jsonContents['usersToNotify'].sort(key = lambda x: x['name'].lower())

        with open(self.__analogueSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent = 4, sort_keys = True)

    def getAnalogueStoreCacheSeconds(self) -> int:
        refreshEverySeconds = self.getRefreshEverySeconds()
        analogueStoreCacheSeconds = int(round(refreshEverySeconds / 2))

        if analogueStoreCacheSeconds < 30:
            raise ValueError(f'Analogue store cache seconds is too aggressive: {analogueStoreCacheSeconds} (\"refreshEverySeconds\": {refreshEverySeconds})')

        return analogueStoreCacheSeconds

    def getChannelIds(self) -> List[int]:
        jsonContents = self.__readJson()
        return jsonContents['channelIds']

    def getPriorityStockProductTypes(self) -> Iterable[AnalogueProductType]:
        productTypes = set()

        for productTypeString in self.getPriorityStockProductStrings():
            if 'dac' == productTypeString.lower():
                productTypes.add(AnalogueProductType.DAC)
            elif 'duo' == productTypeString.lower():
                productTypes.add(AnalogueProductType.DUO)
            elif 'mega sg' == productTypeString.lower():
                productTypes.add(AnalogueProductType.MEGA_SG)
            elif 'nt mini' == productTypeString.lower():
                productTypes.add(AnalogueProductType.NT_MINI)
            elif 'pocket' == productTypeString.lower():
                productTypes.add(AnalogueProductType.POCKET)
            elif 'super nt' == productTypeString.lower():
                productTypes.add(AnalogueProductType.SUPER_NT)

            # Intentionally not adding AnalogueProductType.OTHER to this set. It doesn't
            # really make much sense for an OTHER product type to be something we consider to be a
            # priority item that we're watching out for, since it could be basically anything.

        return productTypes

    def getPriorityStockProductStrings(self) -> Iterable[str]:
        jsonContents = self.__readJson()
        return jsonContents['priorityStockProductTypes']

    def getRefreshDelayAfterPriorityStockFoundSeconds(self) -> int:
        jsonContents = self.__readJson()
        refreshEverySeconds = utils.getIntFromDict(jsonContents, 'refreshEverySeconds')
        refreshDelayAfterPriorityStockFoundSeconds = utils.getIntFromDict(jsonContents, 'refreshDelayAfterPriorityStockFoundSeconds')

        if refreshDelayAfterPriorityStockFoundSeconds <= refreshEverySeconds:
            raise ValueError(f'\"refreshDelayAfterPriorityStockFoundSeconds\" ({refreshDelayAfterPriorityStockFoundSeconds}) must be greater than \"refreshEverySeconds\" ({refreshEverySeconds})')

        return refreshDelayAfterPriorityStockFoundSeconds

    def getRefreshEverySeconds(self) -> int:
        jsonContents = self.__readJson()
        refreshEverySeconds = utils.getIntFromDict(jsonContents, 'refreshEverySeconds')

        if refreshEverySeconds < 60:
            raise ValueError(f'\"refreshEverySeconds\" is too aggressive: {refreshEverySeconds}')

        return refreshEverySeconds

    def getUsersToNotify(self) -> Iterable[User]:
        jsonContents = self.__readJson()
        users = list()

        for userJson in jsonContents['usersToNotify']:
            users.append(User(
                discordDiscriminator = utils.getIntFromDict(userJson, 'discriminator'),
                discordId = utils.getIntFromDict(userJson, 'id'),
                discordName = utils.getStrFromDict(userJson, 'name')
            ))

        return users

    def __readJson(self) -> dict:
        if not os.path.exists(self.__analogueSettingsFile):
            raise FileNotFoundError(f'Analogue settings file not found: \"{self.__analogueSettingsFile}\"')

        with open(self.__analogueSettingsFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Analogue settings file: \"{self.__analogueSettingsFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Analogue settings file \"{self.__analogueSettingsFile}\" is empty')

        return jsonContents

    def removeUser(self, user: User):
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')

        jsonContents = self.__readJson()
        removed = False

        for userJson in jsonContents['usersToNotify']:
            userId = utils.getIntFromDict(userJson, 'id')

            if userId == user.getDiscordId():
                jsonContents['usersToNotify'].remove(userJson)
                removed = True
                break

        if removed:
            with open(self.__analogueSettingsFile, 'w') as file:
                json.dump(jsonContents, file, indent = 4, sort_keys = True)
            return True
        else:
            return False

    def __userToJson(self, user: User) -> dict:
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')

        return {
            'discriminator': user.getDiscordDiscriminator(),
            'id': user.getDiscordId(),
            'name': user.getDiscordName()
        }
