import json
import os
from typing import Dict

import CynanBotCommon.utils as utils


class GeneralSettingsHelper():

    def __init__(
        self,
        generalSettingsFile: str = 'generalSettings.json'
    ):
        if not utils.isValidStr(generalSettingsFile):
            raise ValueError(f'generalSettingsFile argument is malformed: \"{generalSettingsFile}\"')

        self.__generalSettingsFile = generalSettingsFile

    def getRefreshEverySeconds(self) -> int:
        jsonContents = self.__readJson()
        return utils.getIntFromDict(jsonContents, 'refreshEverySeconds')

    def __readJson(self) -> Dict:
        if not os.path.exists(self.__generalSettingsFile):
            raise FileNotFoundError(f'generalSettingsFile not found: \"{self.__generalSettingsFile}\"')

        with open(self.__generalSettingsFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from general settings file: \"{self.__generalSettingsFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of general settings file \"{self.__generalSettingsFile}\" is empty')

        return jsonContents
