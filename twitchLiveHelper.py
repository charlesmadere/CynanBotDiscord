from typing import List

import requests
from requests import ConnectionError, HTTPError, Timeout
from urllib3.exceptions import MaxRetryError, NewConnectionError

import CynanBotCommon.utils as utils
from twitchTokensRepository import TwitchTokensRepository
from user import User


class TwitchLiveHelper():

    def __init__(
        self,
        clientId: str,
        clientSecret: str,
        twitchTokensRepository: TwitchTokensRepository
    ):
        if not utils.isValidStr(clientId):
            raise ValueError(f'clientId argument is malformed: \"{clientId}\"')
        elif not utils.isValidStr(clientSecret):
            raise ValueError(f'clientSecret argument is malformed: \"{clientSecret}\"')
        elif twitchTokensRepository is None:
            raise ValueError(f'twitchTokensRepository argument is malformed: \"{twitchTokensRepository}\"')

        self.__clientId = clientId
        self.__clientSecret = clientSecret
        self.__twitchTokensRepository = twitchTokensRepository

    def whoIsLive(self, users: List[User]) -> List[User]:
        if not utils.hasItems(users):
            return None
        elif len(users) > 100:
            raise ValueError(f'more users than can be asked for from the Twitch API: \"{len(users)}\"')

        print(f'Checking Twitch live status for {len(users)} user(s)... ({utils.getNowTimeText()})')

        userNamesList = list()
        for user in users:
            userNamesList.append(user.getTwitchName())
        userNames = ','.join(userNamesList)

        rawResponse = None
        try:
            rawResponse = requests.get(
                url = f'https://api.twitch.tv/helix/streams?user_login={userNames}',
                headers = {
                    'Client-ID': self.__clientId,
                    'Authorization': f'Bearer {self.__twitchTokensRepository.getAccessToken()}'
                },
                timeout = utils.getDefaultTimeout()
            )
        except (ConnectionError, HTTPError, MaxRetryError, NewConnectionError, Timeout) as e:
            print(f'Exception occurred when attempting to fetch live Twitch streams: {e}')
            raise RuntimeError(f'Exception occurred when attempting to fetch live Twitch streams: {e}')

        jsonResponse = rawResponse.json()
        dataArray = jsonResponse['data']
        whoIsLive = list()

        for dataJson in dataArray:
            userName = dataJson['user_name']

            for user in users:
                if userName.lower() == user.getTwitchName().lower():
                    whoIsLive.append(user)

        return whoIsLive
