import json
import os

import CynanBotCommon.utils as utils
from CynanBotCommon.analogueStoreRepository import AnalogueProductType


class AnalogueSettingsHelper():

    def __init__(self, analogueSettingsFile: str = 'analogueSettings.json'):
        if not utils.isValidStr(analogueSettingsFile):
            raise ValueError(f'analogueSettingsFile argument is malformed: \"{analogueSettingsFile}\"')

        self.__analogueSettingsFile = analogueSettingsFile

    def addUserToUsersToNotify(
        self,
        discriminator: int,
        _id: int,
        name: str
    ):
        if not utils.isValidNum(discriminator):
            raise ValueError(f'discriminator argument is malformed: \"{discriminator}\"')
        elif not utils.isValidNum(_id):
            raise ValueError(f'_id argument is malformed: \"{_id}\"')
        elif not utils.isValidStr(name):
            raise ValueError(f'name argument is malformed: \"{name}\"')

        jsonContents = self.__readJson()
        add = True

        for userJson in jsonContents['usersToNotify']:
            if utils.getIntFromDict(userJson, 'id') == _id:
                userJson['discriminator'] = discriminator
                userJson['name'] = name
                add = False

        if add:
            jsonContents['usersToNotify'].append({
                'discriminator': discriminator,
                'id': _id,
                'name': name
            })

        with open(self.__analogueSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent=4, sort_keys=True)

        print(f'Saved new user \"{name}#{discriminator}\" (ID {_id}) as a user to notify ({utils.getNowTimeText()})')

    def getChannelId(self):
        jsonContents = self.__readJson()
        return utils.getIntFromDict(jsonContents, 'channelId')

    def getPriorityStockProductTypes(self):
        jsonContents = self.__readJson()
        productTypeStrings = jsonContents['priorityStockProductTypes']

        productTypes = set()
        for productTypeString in productTypeStrings:
            if productTypeString.lower() == 'dac':
                productTypes.add(AnalogueProductType.DAC)
            elif productTypeString.lower() == 'duo':
                productTypes.add(AnalogueProductType.DUO)
            elif productTypeString.lower() == 'mega sg':
                productTypes.add(AnalogueProductType.MEGA_SG)
            elif productTypeString.lower() == 'nt mini':
                productTypes.add(AnalogueProductType.NT_MINI)
            elif productTypeString.lower() == 'pocket':
                productTypes.add(AnalogueProductType.POCKET)
            elif productTypeString.lower() == 'super nt':
                productTypes.add(AnalogueProductType.SUPER_NT)

        return productTypes

    def getRefreshEveryMinutes(self):
        jsonContents = self.__readJson()
        return utils.getIntFromDict(jsonContents, 'refreshEveryMinutes')

    def getRefreshEverySeconds(self):
        return self.getRefreshEveryMinutes() * 60

    def getUsersToNotify(self):
        jsonContents = self.__readJson()
        users = list()

        for userJson in jsonContents['usersToNotify']:
            users.append(AnalogueUserToNotify(
                discriminator=utils.getIntFromDict(userJson, 'discriminator'),
                _id=utils.getIntFromDict(userJson, 'id'),
                name=utils.getStrFromDict(userJson, 'name')
            ))

        return users

    def __readJson(self):        
        if not os.path.exists(self.__analogueSettingsFile):
            raise FileNotFoundError(f'Analogue settings file not found: \"{self.__analogueSettingsFile}\"')

        with open(self.__analogueSettingsFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Analogue settings file: \"{self.__analogueSettingsFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Analogue Settings file \"{self.__analogueSettingsFile}\" is empty')

        return jsonContents

    def removeUserFromUsersToNotify(self, _id: int):
        if not utils.isValidNum(_id):
            raise ValueError(f'_id argument is malformed: \"{_id}\"')

        jsonContents = self.__readJson()

        for userJson in jsonContents['usersToNotify']:
            if utils.getIntFromDict(userJson, 'id') == _id:
                jsonContents['usersToNotify'].remove(userJson)
                break

        with open(self.__analogueSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent=4, sort_keys=True)

        print(f'Removed user (ID {_id}) from users to notify ({utils.getNowTimeText()})')


class AnalogueUserToNotify():

    def __init__(
        self,
        discriminator: int,
        _id: int,
        name: str
    ):
        if not utils.isValidNum(discriminator):
            raise ValueError(f'discriminator argument is malformed: {discriminator}')
        elif not utils.isValidNum(_id):
            raise ValueError(f'_id argument is malformed: \"{_id}\"')
        elif not utils.isValidStr(name):
            raise ValueError(f'name argument is malformed: \"{name}\"')

        self.__discriminator = discriminator
        self.__id = _id
        self.__name = name

    def getDiscriminator(self): 
        return self.__discriminator

    def getId(self):
        return self.__id

    def getName(self):
        return self.__name

    def getNameAndDiscriminator(self):
        return f'{self.__name}#{self.__discriminator}'

    def toStr(self):
        return f'{self.getNameAndDiscriminator()} ({self.__id})'
