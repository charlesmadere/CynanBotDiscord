from typing import Dict, List

import requests
from requests import ConnectionError, HTTPError, Timeout
from urllib3.exceptions import MaxRetryError, NewConnectionError

import CynanBotCommon.utils as utils
from twitchTokensRepository import TwitchTokensRepository
from user import User


class TwitchLiveData():

    def __init__(
        self,
        streamId: str,
        userId: str,
        userLogin: str,
        userName: str,
        viewerCount: int = None,
        gameId: str = None,
        gameName: str = None,
        language: str = None,
        streamType: str = None,
        thumbnailUrl: str = None,
        title: str = None
    ):
        if not utils.isValidStr(streamId):
            raise ValueError(f'streamId argument is malformed: \"{streamId}\"')
        elif not utils.isValidStr(userId):
            raise ValueError(f'userId argument is malformed: \"{userId}\"')
        elif not utils.isValidStr(userLogin):
            raise ValueError(f'userLogin argument is malformed: \"{userLogin}\"')
        elif not utils.isValidStr(userName):
            raise ValueError(f'userName argument is malformed: \"{userName}\"')

        self.__streamId = streamId
        self.__userId = userId
        self.__userLogin = userLogin
        self.__userName = userName
        self.__viewerCount = viewerCount
        self.__gameId = gameId
        self.__gameName = gameName
        self.__language = language
        self.__streamType = streamType
        self.__thumbnailUrl = thumbnailUrl
        self.__title = title

    def getGameId(self) -> str:
        return self.__gameId

    def getGameName(self) -> str:
        return self.__gameName

    def getLanguage(self) -> str:
        return self.__language

    def getStreamId(self) -> str:
        return self.__streamId

    def getStreamType(self) -> str:
        return self.__streamType

    def getThumbnailUrl(self) -> str:
        return self.__thumbnailUrl

    def getTitle(self) -> str:
        return self.__title

    def getUserId(self) -> str:
        return self.__userId

    def getUserLogin(self) -> str:
        return self.__userLogin

    def getUserName(self) -> str:
        return self.__userName

    def getViewerCount(self) -> int:
        return self.__viewerCount

    def hasGameId(self) -> bool:
        return utils.isValidStr(self.__gameId)

    def hasGameName(self) -> bool:
        return utils.isValidStr(self.__gameName)

    def hasLanguage(self) -> bool:
        return utils.isValidStr(self.__language)

    def hasStreamType(self) -> bool:
        return utils.isValidStr(self.__streamType)

    def hasThumbnailUrl(self) -> str:
        return utils.isValidUrl(self.__thumbnailUrl)

    def hasTitle(self) -> bool:
        return utils.isValidStr(self.__title)

    def hasViewerCount(self) -> bool:
        return utils.isValidNum(self.__viewerCount)

    def isStreamTypeLive(self) -> bool:
        return self.hasStreamType() and self.__streamType == 'live'


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

    def whoIsLive(self, users: List[User]) -> Dict[User, TwitchLiveData]:
        if not utils.hasItems(users):
            return None
        elif len(users) > 100:
            raise ValueError(f'more users than can be asked for from the Twitch API: \"{len(users)}\"')

        print(f'Checking Twitch live status for {len(users)} user(s)... ({utils.getNowTimeText()})')

        userNamesList = list()
        for user in users:
            userNamesList.append(user.getTwitchName())
        userNames = '&user_login='.join(userNamesList)

        rawResponse = None
        try:
            rawResponse = requests.get(
                url = f'https://api.twitch.tv/helix/streams?user_login={userNames}',
                headers = {
                    'Client-Id': self.__clientId,
                    'Authorization': f'Bearer {self.__twitchTokensRepository.getAccessToken()}'
                },
                timeout = utils.getDefaultTimeout()
            )
        except (ConnectionError, HTTPError, MaxRetryError, NewConnectionError, Timeout) as e:
            print(f'Exception occurred when attempting to fetch live Twitch streams: {e}')
            raise RuntimeError(f'Exception occurred when attempting to fetch live Twitch streams: {e}')

        jsonResponse = rawResponse.json()

        if 'error' in jsonResponse and len(jsonResponse['error']) >= 1 or 'data' not in jsonResponse:
            print(f'Error when checking Twitch live status for {len(users)} user(s)! {jsonResponse}')

            if 'status' in jsonResponse and jsonResponse['status'] == 401:
                self.__twitchTokensRepository.validateAndRefreshAccessToken(
                    clientId = self.__clientId,
                    clientSecret = self.__clientSecret
                )

                return self.whoIsLive(users)
            else:
                raise RuntimeError(f'Unknown error returned by Twitch API')

        dataArray = jsonResponse['data']
        if not utils.hasItems(dataArray):
            return None

        whoIsLive = dict()

        for dataJson in dataArray:
            twitchLiveData = TwitchLiveData(
                streamId = dataJson['id'],
                userId = dataJson['user_id'],
                userLogin = dataJson['user_login'],
                userName = dataJson['user_name'],
                viewerCount = dataJson.get('viewer_count'),
                gameId = dataJson.get('game_id'),
                gameName = dataJson.get('game_name'),
                language = dataJson.get('language'),
                streamType = dataJson.get('type'),
                thumbnailUrl = dataJson.get('thumbnail_url'),
                title = dataJson.get('title')
            )

            if twitchLiveData.isStreamTypeLive():
                userName = twitchLiveData.getUserName().lower()

                for user in users:
                    if userName == user.getTwitchName().lower():
                        whoIsLive[user] = twitchLiveData

        print(f'Number of users live on Twitch: {len(whoIsLive)}')
        return whoIsLive
