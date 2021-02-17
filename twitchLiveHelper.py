from typing import List

import requests
from requests import ConnectionError, HTTPError, Timeout
from urllib3.exceptions import MaxRetryError, NewConnectionError

import CynanBotCommon.utils as utils
from twitchAccounceSettingsHelper import TwitchAnnounceUser


class TwitchLiveHelper():

    def __init__(
        self,
        clientId: str
    ):
        if not utils.isValidStr(clientId):
            raise ValueError(f'clientId argument is malformed: \"{clientId}\"')

        self.__clientId = clientId

    def isLive(self, users: List[TwitchAnnounceUser]) -> dict[TwitchAnnounceUser, bool]:
        if not utils.hasItems(users):
            raise ValueError(f'users argument is malformed: \"{users}\"')

        isLiveDict = dict()

        # TODO
        rawResponse = None
        try:
            rawResponse = requests.get(
                url = f'https://api.twitch.tv/helix/streams',
                headers = {
                    'Client-ID': self.__clientId
                },
                timeout = utils.getDefaultTimeout()
            )
        except (ConnectionError, HTTPError, MaxRetryError, NewConnectionError, Timeout) as e:
            print(f'Exception occurred when attempting to fetch live Twitch streams: {e}')
            raise RuntimeError(f'Exception occurred when attempting to fetch live Twitch streams: {e}')

        jsonResponse = rawResponse.json()

        return isLiveDict
