import json
import os

import CynanBotCommon.utils as utils
from CynanBotCommon.analogueStoreRepository import AnalogueProductType


class AnalogueSettingsHelper():

    def __init__(self, analogueSettingsFile: str = 'analogueSettings.json'):
        if not utils.isValidStr(analogueSettingsFile):
            raise ValueError(f'analogueSettingsFile argument is malformed: \"{analogueSettingsFile}\"')

        self.__analogueSettingsFile = analogueSettingsFile

    def getChannelId(self):
        jsonContents = self.__readJson()
        channelId = jsonContents['channelId']

        if not utils.isValidStr(channelId):
            raise ValueError(f'channelId is malformed: \"{channelId}\"')

        return channelId

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
