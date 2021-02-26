import json
import os
from typing import Dict

import CynanBotCommon.utils as utils
from CynanBotCommon.analogueStoreRepository import AnalogueProductType


class AnalogueSettingsHelper():

    def __init__(
        self,
        analogueSettingsFile: str = 'analogueSettings.json'
    ):
        if not utils.isValidStr(analogueSettingsFile):
            raise ValueError(f'analogueSettingsFile argument is malformed: \"{analogueSettingsFile}\"')

        self.__analogueSettingsFile = analogueSettingsFile

    def getAnalogueStoreCacheSeconds(self) -> int:
        refreshEverySeconds = self.getRefreshEverySeconds()
        analogueStoreCacheSeconds = int(round(refreshEverySeconds / 2))

        if analogueStoreCacheSeconds < 30:
            raise ValueError(f'Analogue store cache seconds is too aggressive: {analogueStoreCacheSeconds} (\"refreshEverySeconds\": {refreshEverySeconds})')

        return analogueStoreCacheSeconds

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

    def __readJson(self) -> Dict:
        if not os.path.exists(self.__analogueSettingsFile):
            raise FileNotFoundError(f'Analogue settings file not found: \"{self.__analogueSettingsFile}\"')

        with open(self.__analogueSettingsFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Analogue settings file: \"{self.__analogueSettingsFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Analogue settings file \"{self.__analogueSettingsFile}\" is empty')

        return jsonContents
