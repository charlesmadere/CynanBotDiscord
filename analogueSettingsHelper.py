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

        # dancing between set and list in order to prevent duplicates
        usersSet = set(jsonContents['usersToNotify'])
        usersSet.add(user)
        usersList = list(usersSet)
        usersList.sort()

        # make sure to use a list here, an exception will occur if you try to write a set to the JSON
        jsonContents['usersToNotify'] = usersList

        with open(self.__analogueSettingsFile, 'w') as file:
            json.dump(jsonContents, file, indent=4, sort_keys=True)

        print(f'Saved new user \"{user}\" as a user to notify ({utils.getNowTimeText()})')

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
