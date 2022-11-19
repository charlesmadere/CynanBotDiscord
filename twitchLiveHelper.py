import locale
from json.decoder import JSONDecodeError
from typing import Any, Dict, List, Optional

import aiohttp

import CynanBotCommon.utils as utils
from authRepository import AuthRepository
from CynanBotCommon.networkClientProvider import NetworkClientProvider
from CynanBotCommon.timber.timber import Timber
from CynanBotCommon.twitch.twitchTokensRepository import TwitchTokensRepository
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

        self.__streamId: str = streamId
        self.__userId: str = userId
        self.__userLogin: str = userLogin
        self.__userName: str = userName
        self.__viewerCount: int = viewerCount
        self.__gameId: str = gameId
        self.__gameName: str = gameName
        self.__language: str = language
        self.__streamType: str = streamType
        self.__thumbnailUrl: str = thumbnailUrl
        self.__title: str = title

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
        authRepository: AuthRepository,
        networkClientProvider: NetworkClientProvider,
        timber: Timber,
        twitchTokensRepository: TwitchTokensRepository,
        twitchHandle: str = 'CynanBot'
    ):
        if authRepository is None:
            raise ValueError(f'authRepository argument is malformed: \"{authRepository}\"')
        elif networkClientProvider is None:
            raise ValueError(f'networkClientProvider argument is malformed: \"{networkClientProvider}\"')
        elif timber is None:
            raise ValueError(f'timber argument is malformed: \"{timber}\"')
        elif twitchTokensRepository is None:
            raise ValueError(f'twitchTokensRepository argument is malformed: \"{twitchTokensRepository}\"')
        elif not utils.isValidStr(twitchHandle):
            raise ValueError(f'twitchHandle argument is malformed: \"{twitchHandle}\"')

        self.__authRepository: AuthRepository = authRepository
        self.__networkClientProvider: NetworkClientProvider = networkClientProvider
        self.__timber: Timber = timber
        self.__twitchTokensRepository: TwitchTokensRepository = twitchTokensRepository
        self.__twitchHandle: str = twitchHandle

    async def fetchWhoIsLive(self, users: List[User]) -> Optional[Dict[User, TwitchLiveData]]:
        return await self.__fetchWhoIsLive(users = users, isRetry = False)

    async def __fetchWhoIsLive(self, users: List[User], isRetry: bool) -> Optional[Dict[User, TwitchLiveData]]:
        if not utils.isValidBool(isRetry):
            raise ValueError(f'isRetry argument is malformed: \"{isRetry}\"')

        if not utils.hasItems(users):
            return None
        elif len(users) > 100:
            raise ValueError(f'more users than can be asked for from the Twitch API: \"{len(users)}\"')

        self.__timber.log('TwitchLiveHelper', f'Checking Twitch live status for {len(users)} user(s)...')

        userNamesList: List[str] = list()
        for user in users:
            userNamesList.append(user.getTwitchName())
        userNamesStr: str = '&user_login='.join(userNamesList)

        clientSession = await self.__networkClientProvider.get()
        twitchAccessToken = await self.__twitchTokensRepository.requireAccessToken(self.__twitchHandle)
        authSnapshot = await self.__authRepository.getAllAsync()
        twitchClientId = authSnapshot.requireTwitchClientId()
        twitchClientSecret = authSnapshot.requireTwitchClientSecret()

        rawResponse = None
        try:
            rawResponse = await clientSession.get(
                url = f'https://api.twitch.tv/helix/streams?user_login={userNamesStr}',
                headers = {
                    'Authorization': f'Bearer {twitchAccessToken}',
                    'Client-Id': twitchClientId
                }
            )
        except (aiohttp.ClientError, TimeoutError) as e:
            self.__timber.log('TwitchLiveHelper', f'Exception occurred when attempting to fetch live Twitch stream(s) for {len(users)} user(s): {e}', e)
            raise RuntimeError(f'Exception occurred when attempting to fetch live Twitch stream(s) for {len(users)} user(s): {e}')

        jsonResponse: Optional[Dict[str, Any]] = None
        try:
            jsonResponse = await rawResponse.json()
        except JSONDecodeError as e:
            self.__timber.log('TwitchLiveHelper', f'Exception occurred when attempting to decode Twitch\'s response into JSON: {e}', e)
            raise RuntimeError(f'Exception occurred when attempting to decode Twitch\'s response into JSON: {e}')

        if 'error' in jsonResponse and len(jsonResponse['error']) >= 1 or 'data' not in jsonResponse:
            self.__timber.log('TwitchLiveHelper', f'Error when checking Twitch live status for {len(users)} user(s)! {jsonResponse}')

            if isRetry:
                raise RuntimeError(f'We\'re already in the middle of a retry, this could be an infinite loop!')
            elif 'status' in jsonResponse and utils.getIntFromDict(jsonResponse, 'status') == 401:
                await self.__twitchTokensRepository.validateAndRefreshAccessToken(
                    twitchClientId = twitchClientId,
                    twitchClientSecret = twitchClientSecret,
                    twitchHandle = self.__twitchHandle
                )

                return await self.__fetchWhoIsLive(users = users, isRetry = True)
            else:
                raise RuntimeError(f'Unknown error returned by Twitch API: {jsonResponse}')

        dataArray: Optional[List[Dict[str, Any]]] = jsonResponse.get('data')
        if not utils.hasItems(dataArray):
            return None

        whoIsLive: Dict[User, TwitchLiveData] = dict()
        whoIsLiveUserLogins: List[str] = list()

        for dataJson in dataArray:
            twitchLiveData = TwitchLiveData(
                streamId = utils.getStrFromDict(dataJson, 'id'),
                userId = utils.getStrFromDict(dataJson, 'user_id'),
                userLogin = utils.getStrFromDict(dataJson, 'user_login'),
                userName = utils.getStrFromDict(dataJson, 'user_name'),
                viewerCount = dataJson.get('viewer_count'),
                gameId = dataJson.get('game_id'),
                gameName = dataJson.get('game_name'),
                language = dataJson.get('language'),
                streamType = dataJson.get('type'),
                thumbnailUrl = dataJson.get('thumbnail_url'),
                title = dataJson.get('title')
            )

            if twitchLiveData.isStreamTypeLive():
                userLogin = twitchLiveData.getUserLogin().lower()
                userName = twitchLiveData.getUserName().lower()
                whoIsLiveUserLogins.append(twitchLiveData.getUserLogin())

                for user in users:
                    twitchName = user.getTwitchName().lower()

                    # We check both userLogin and userName because some multi-language users
                    # could have very different names between userLogin and userName. For example,
                    # a Korean user may have a userName written using actual Korean characters,
                    # and then a userLogin written in English characters.
                    if userLogin == twitchName or userName == twitchName:
                        whoIsLive[user] = twitchLiveData

        whoIsLiveUserLoginsString = ', '.join(whoIsLiveUserLogins)
        self.__timber.log('TwitchLiveHelper', f'{len(whoIsLive)} user(s) live on Twitch: {whoIsLiveUserLoginsString}')

        if len(whoIsLive) != len(whoIsLiveUserLogins):
            self.__timber.log('TwitchLiveHelper', f'Encountered a data error of some kind, outputting some debug information: {jsonResponse}')

        return whoIsLive
