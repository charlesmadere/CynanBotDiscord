from typing import Any, Dict

import CynanBotCommon.utils as utils


class TwitchAnnounceSettingsSnapshot():

    def __init__(
        self,
        jsonContents: Dict[str, Any],
        twitchAnnounceSettingsFile: str
    ):
        if not utils.hasItems(jsonContents):
            raise ValueError(f'jsonContents argument is malformed: \"{jsonContents}\"')
        elif not utils.isValidStr(twitchAnnounceSettingsFile):
            raise ValueError(f'twitchAnnounceSettingsFile argument is malformed: \"{twitchAnnounceSettingsFile}\"')

        self.__jsonContents: Dict[str, Any] = jsonContents
        self.__twitchAnnounceSettingsFile: str = twitchAnnounceSettingsFile

    def getAnnounceFalloffMinutes(self) -> int:
        announceFalloffMinutes = utils.getIntFromDict(self.__jsonContents, 'announceFalloffMinutes', 60)

        if announceFalloffMinutes < 30:
            raise ValueError(f'\"announceFalloffMinutes\" is too aggressive: {announceFalloffMinutes}')

        return announceFalloffMinutes

    def getRefreshEveryMinutes(self) -> int:
        refreshEveryMinutes = utils.getIntFromDict(self.__jsonContents, 'refreshEveryMinutes', 5)

        if refreshEveryMinutes < 5:
            raise ValueError(f'\"refreshEveryMinutes\" is too aggressive: {refreshEveryMinutes}')

        return refreshEveryMinutes
