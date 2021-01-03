import json
import os

import CynanBotCommon.utils as utils
from CynanBotCommon.analogueStoreRepository import AnalogueProductType


class AnalogueSettingsHelper():

    def __init__(self, analogueSettingsFile: str = 'analogueSettings.json'):
        if not utils.isValidStr(analogueSettingsFile):
            raise ValueError(f'analogueSettingsFile argument is malformed: \"{analogueSettingsFile}\"')

        self.__analogueSettingsFile = analogueSettingsFile

    def addUserToUsersToNotify(self, user: str):
        if not utils.isValidStr(user):
            raise ValueError(f'user argument is malformed: \"{user}\"')

        if not os.path.exists(self.__analogueSettingsFile):
            raise FileNotFoundError(f'Analogue settings file not found: \"{self.__analogueSettingsFile}\"')

        with open(self.__analogueSettingsFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Analogue settings file: \"{self.__analogueSettingsFile}\"')

        users = jsonContents['usersToNotify']

        for existingUser in users:
            if existingUser.lower() == user.lower():
                raise RuntimeError(f'User \"{user}\" is already set as a user to notify')

        users.append(user)

        with open(self.__analogueSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent=4, sort_keys=True)

        print(f'Saved new user \"{user}\" as a user to notify ({utils.getNowTimeText()})')

    def getChannelId(self):
        jsonContents = self.__readJson()
        return utils.getIntFromDict(jsonContents, 'channelId')

    def getPriorityStockProductTypes(self):
        jsonContents = self.__readJson()
        productTypeStrings = jsonContents['priorityStockProductTypes']

        productTypes = list()
        for productTypeString in productTypeStrings:
            if productTypeString.lower() == 'mega sg':
                productTypes.append(AnalogueProductType.MEGA_SG)
            elif productTypeString.lower() == 'nt mini':
                productTypes.append(AnalogueProductType.NT_MINI)
            elif productTypeString.lower() == 'pocket':
                productTypes.append(AnalogueProductType.POCKET)
            elif productTypeString.lower() == 'super nt':
                productTypes.append(AnalogueProductType.SUPER_NT)

        return productTypes

    def getRefreshEveryMinutes(self):
        jsonContents = self.__readJson()
        return utils.getIntFromDict(jsonContents, 'refreshEveryMinutes')

    def getRefreshEverySeconds(self):
        return self.getRefreshEveryMinutes() * 60

    def getUsersToNotify(self):
        jsonContents = self.__readJson()
        return jsonContents['usersToNotify']

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
