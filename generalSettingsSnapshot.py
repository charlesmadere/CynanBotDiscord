from typing import Any, Dict

import CynanBotCommon.utils as utils
from CynanBotCommon.storage.databaseType import DatabaseType


class GeneralSettingsSnapshot():

    def __init__(
        self,
        jsonContents: Dict[str, Any],
        generalSettingsFile: str
    ):
        if not utils.hasItems(jsonContents):
            raise ValueError(f'jsonContents argument is malformed: \"{jsonContents}\"')
        elif not utils.isValidStr(generalSettingsFile):
            raise ValueError(f'generalSettingsFile argument is malformed: \"{generalSettingsFile}\"')

        self.__jsonContents: Dict[str, Any] = jsonContents
        self.__generalSettingsFile: str = generalSettingsFile

    def getRefreshEverySeconds(self) -> int:
        return utils.getIntFromDict(self.__jsonContents, 'refreshEverySeconds')

    def requireDatabaseType(self) -> DatabaseType:
        databaseType = self.__jsonContents.get('databaseType')

        if not utils.isValidStr(databaseType):
            raise ValueError(f'\"databaseType\" in general settings file (\"{self.__generalSettingsFile}\") is malformed: \"{databaseType}\"')

        return DatabaseType.fromStr(databaseType)
