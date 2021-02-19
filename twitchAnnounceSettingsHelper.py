import json
import os

import CynanBotCommon.utils as utils


class TwitchAnnounceSettingsHelper():

    def __init__(
        self,
        twitchAnnounceSettingsFile: str = 'twitchAnnounceSettings.json'
    ):
        if not utils.isValidStr(twitchAnnounceSettingsFile):
            raise ValueError(f'twitchAnnounceSettingsFile argument is malformed: \"{twitchAnnounceSettingsFile}\"')

        self.__twitchAnnounceSettingsFile = twitchAnnounceSettingsFile

    def getAnnounceFalloffMinutes(self) -> int:
        jsonContents = self.__readJson()
        announceFalloffMinutes = utils.getIntFromDict(jsonContents, 'announceFalloffMinutes')

        if announceFalloffMinutes < 30:
            raise ValueError(f'\"announceFalloffMinutes\" is too aggressive: {announceFalloffMinutes}')

        return announceFalloffMinutes

    def getRefreshEveryMinutes(self) -> int:
        jsonContents = self.__readJson()
        refreshEveryMinutes = utils.getIntFromDict(jsonContents, 'refreshEveryMinutes')

        if refreshEveryMinutes < 5:
            raise ValueError(f'\"refreshEveryMinutes\" is too aggressive: {refreshEveryMinutes}')

        return refreshEveryMinutes

    def __readJson(self) -> dict:
        if not os.path.exists(self.__twitchAnnounceSettingsFile):
            raise FileNotFoundError(f'Twitch announce settings file not found: \"{self.__twitchAnnounceSettingsFile}\"')

        with open(self.__twitchAnnounceSettingsFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Twitch announce settings file: \"{self.__twitchAnnounceSettingsFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Twitch announce settings file \"{self.__twitchAnnounceSettingsFile}\" is empty')

        return jsonContents
