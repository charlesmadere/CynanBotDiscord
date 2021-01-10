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

        user = AnalogueUserToNotify(
            discriminator=discriminator,
            _id=_id,
            name=name
        )

        for userJson in jsonContents['usersToNotify']:
            if utils.getIntFromDict(userJson, 'id') == user.getId():
                userJson['discriminator'] = user.getDiscriminator()
                userJson['name'] = user.getName()
                add = False

        if add:
            jsonContents['usersToNotify'].append(user.toJsonDict())

        jsonContents['usersToNotify'].sort(key=lambda x: x['name'])

        with open(self.__analogueSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent=4, sort_keys=True)

        return user

    def getChannelId(self):
        jsonContents = self.__readJson()
        return utils.getIntFromDict(jsonContents, 'channelId')

    def getPriorityStockProductTypes(self):
        jsonContents = self.__readJson()
        productTypes = set()

        for productTypeString in jsonContents['priorityStockProductTypes']:
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
        refreshEveryMinutes = utils.getIntFromDict(jsonContents, 'refreshEveryMinutes')

        if refreshEveryMinutes < 1:
            raise ValueError(f'\"refreshEveryMinutes\" is an illegal value: {refreshEveryMinutes}')

        return refreshEveryMinutes

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
        user = None

        for userJson in jsonContents['usersToNotify']:
            userId = utils.getIntFromDict(userJson, 'id')

            if userId == _id:
                user = AnalogueUserToNotify(
                    discriminator=userJson['discriminator'],
                    _id=userId,
                    name=userJson['name']
                )

                jsonContents['usersToNotify'].remove(userJson)
                break

        with open(self.__analogueSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent=4, sort_keys=True)

        return user


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

    def toJsonDict(self):
        return {
            'discriminator': self.__discriminator,
            'id': self.__id,
            'name': self.__name
        }

    def toStr(self):
        return f'{self.getNameAndDiscriminator()} ({self.__id})'
