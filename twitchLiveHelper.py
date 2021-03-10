import locale
from json.decoder import JSONDecodeError
from typing import Dict, List

import requests
from requests import ConnectionError, HTTPError, Timeout
from urllib3.exceptions import MaxRetryError, NewConnectionError

import CynanBotCommon.utils as utils
from CynanBotCommon.twitchTokensRepository import TwitchTokensRepository
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

    def getViewerCountStr(self) -> str:
        if self.hasViewerCount():
            return locale.format_string("%d", self.__viewerCount, grouping = True)
        else:
            raise RuntimeError(f'This TwitchLiveData ({self}) does not have a viewerCount value!')

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
        twitchClientId: str,
        twitchClientSecret: str,
        twitchTokensRepository: TwitchTokensRepository,
        twitchHandle: str = 'CynanBot'
    ):
        if not utils.isValidStr(twitchClientId):
            raise ValueError(f'twitchClientId argument is malformed: \"{twitchClientId}\"')
        elif not utils.isValidStr(twitchClientSecret):
            raise ValueError(f'twitchClientSecret argument is malformed: \"{twitchClientSecret}\"')
        elif twitchTokensRepository is None:
            raise ValueError(f'twitchTokensRepository argument is malformed: \"{twitchTokensRepository}\"')
        elif not utils.isValidStr(twitchHandle):
            raise ValueError(f'twitchHandle argument is malformed: \"{twitchHandle}\"')

        self.__twitchClientId = twitchClientId
        self.__twitchClientSecret = twitchClientSecret
        self.__twitchTokensRepository = twitchTokensRepository
        self.__twitchHandle = twitchHandle

    def fetchWhoIsLive(self, users: List[User]) -> Dict[User, TwitchLiveData]:
        return self.__fetchWhoIsLive(users = users, isRetry = False)

    def __fetchWhoIsLive(self, users: List[User], isRetry: bool) -> Dict[User, TwitchLiveData]:
        if isRetry is None:
            raise ValueError(f'isRetry argument is malformed: \"{isRetry}\"')

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
                    'Client-Id': self.__twitchClientId,
                    'Authorization': f'Bearer {self.__twitchTokensRepository.getAccessToken(self.__twitchHandle)}'
                },
                timeout = utils.getDefaultTimeout()
            )
        except (ConnectionError, HTTPError, MaxRetryError, NewConnectionError, Timeout) as e:
            print(f'Exception occurred when attempting to fetch live Twitch streams: {e}')
            raise RuntimeError(f'Exception occurred when attempting to fetch live Twitch streams: {e}')

        jsonResponse = None
        try:
            jsonResponse = rawResponse.json()
        except JSONDecodeError as e:
            print(f'Exception occurred when attempting to decode Twitch\'s response into JSON: {e}')
            raise RuntimeError(f'Exception occurred when attempting to decode Twitch\'s response into JSON: {e}')

        if 'error' in jsonResponse and len(jsonResponse['error']) >= 1 or 'data' not in jsonResponse:
            print(f'Error when checking Twitch live status for {len(users)} user(s)! {jsonResponse}')

            if isRetry:
                raise RuntimeError(f'We\'re already in the middle of a retry, this could be an infinite loop!')
            elif 'status' in jsonResponse and jsonResponse['status'] == 401:
                self.__twitchTokensRepository.validateAndRefreshAccessToken(
                    twitchClientId = self.__twitchClientId,
                    twitchClientSecret = self.__twitchClientSecret,
                    twitchHandle = self.__twitchHandle
                )

                return self.__fetchWhoIsLive(users = users, isRetry = True)
            else:
                raise RuntimeError(f'Unknown error returned by Twitch API: {jsonResponse}')

        dataArray = jsonResponse['data']
        if not utils.hasItems(dataArray):
            return None

        whoIsLive = dict()
        whoIsLiveUserNames = list()

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
                whoIsLiveUserNames.append(twitchLiveData.getUserName())

                for user in users:
                    if userName == user.getTwitchName().lower():
                        whoIsLive[user] = twitchLiveData

        whoIsLiveUserNamesString = ', '.join(whoIsLiveUserNames)
        print(f'{len(whoIsLive)} user(s) live on Twitch: {whoIsLiveUserNamesString}')
        return whoIsLive
