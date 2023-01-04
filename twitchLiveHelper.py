from typing import Dict, List, Optional

import CynanBotCommon.utils as utils
from CynanBotCommon.network.exceptions import GenericNetworkException
from CynanBotCommon.timber.timber import Timber
from CynanBotCommon.twitch.exceptions import TwitchTokenIsExpiredException
from CynanBotCommon.twitch.twitchApiService import TwitchApiService
from CynanBotCommon.twitch.twitchLiveUserDetails import TwitchLiveUserDetails
from CynanBotCommon.twitch.twitchStreamType import TwitchStreamType
from CynanBotCommon.twitch.twitchTokensRepository import TwitchTokensRepository
from user import User


class TwitchLiveHelper():

    def __init__(
        self,
        timber: Timber,
        twitchApiService: TwitchApiService,
        twitchTokensRepository: TwitchTokensRepository,
        maxRetryCount: int = 3,
        twitchHandle: str = 'CynanBot'
    ):
        if not isinstance(timber, Timber):
            raise ValueError(f'timber argument is malformed: \"{timber}\"')
        elif not isinstance(twitchApiService, TwitchApiService):
            raise ValueError(f'twitchApiService argument is malformed: \"{twitchApiService}\"')
        elif not isinstance(twitchTokensRepository, TwitchTokensRepository):
            raise ValueError(f'twitchTokensRepository argument is malformed: \"{twitchTokensRepository}\"')
        elif not utils.isValidInt(maxRetryCount):
            raise ValueError(f'retryCount argument is malformed: \"{maxRetryCount}\"')
        elif maxRetryCount < 3 or maxRetryCount > 5:
            raise ValueError(f'maxRetryCount argument is out of bounds: {maxRetryCount}')
        elif not utils.isValidStr(twitchHandle):
            raise ValueError(f'twitchHandle argument is malformed: \"{twitchHandle}\"')

        self.__timber: Timber = timber
        self.__twitchApiService: TwitchApiService = twitchApiService
        self.__twitchTokensRepository: TwitchTokensRepository = twitchTokensRepository
        self.__maxRetryCount: int = maxRetryCount
        self.__twitchHandle: str = twitchHandle

    async def fetchWhoIsLive(
        self,
        users: List[User]
    ) -> Optional[Dict[User, TwitchLiveUserDetails]]:
        if not utils.hasItems(users):
            return None
        elif len(users) > 100:
            raise ValueError(f'more users than can be asked for from the Twitch API: \"{len(users)}\"')

        self.__timber.log('TwitchLiveHelper', f'Checking Twitch live status for {len(users)} user(s)...')

        userNames: List[str] = list()
        for user in users:
            userNames.append(user.getTwitchName())

        retryCount = 0
        liveUserDetails: Optional[List[TwitchLiveUserDetails]] = None

        while liveUserDetails is None and retryCount < self.__maxRetryCount:
            retryCount = retryCount + 1
            twitchAccessToken = await self.__twitchTokensRepository.requireAccessToken(self.__twitchHandle)

            try:
                liveUserDetails = await self.__twitchApiService.fetchLiveUserDetails(
                    twitchAccessToken = twitchAccessToken,
                    userNames = userNames
                )
            except GenericNetworkException as e:
                self.__timber.log('TwitchLiveHelper', f'General network exception occurred (retryCount={retryCount}) when attempting to fetch live Twitch stream(s) for {len(users)} user(s): {e}', e)
            except TwitchTokenIsExpiredException as e:
                self.__timber.log('TwitchLiveHelper', f'Twitch token exception occurred (retryCount={retryCount}) when attempting to fetch live Twitch stream(s) for {len(users)} user(s): {e}', e)
                await self.__twitchTokensRepository.validateAndRefreshAccessToken(
                    twitchHandle = self.__twitchHandle
                )

        if liveUserDetails is None:
            self.__timber.log('TwitchLiveHelper', f'Unable to fetch who is live Twitch stream(s) for {len(users)} user(s) after {retryCount} attempt(s)')
            return None

        whoIsLive: Dict[User, TwitchLiveUserDetails] = dict()
        whoIsLiveUserLogins: List[str] = list()

        for liveUser in liveUserDetails:
            if liveUser.getStreamType() is not TwitchStreamType.LIVE:
                continue

            userLogin = liveUser.getUserLogin().lower()
            userName = liveUser.getUserName().lower()
            whoIsLiveUserLogins.append(liveUser.getUserLogin())

            for user in users:
                twitchName = user.getTwitchName().lower()

                # We check both userLogin and userName because some multi-language users
                # could have very different names between userLogin and userName. For example,
                # a Korean user may have a userName written using actual Korean characters,
                # and then a userLogin written in English characters.
                if userLogin == twitchName or userName == twitchName:
                    whoIsLive[user] = liveUserDetails

        whoIsLiveUserLoginsString = ', '.join(whoIsLiveUserLogins)
        self.__timber.log('TwitchLiveHelper', f'{len(whoIsLive)} user(s) live on Twitch: {whoIsLiveUserLoginsString}')

        if len(whoIsLive) != len(whoIsLiveUserLogins):
            self.__timber.log('TwitchLiveHelper', f'Encountered a data error of some kind, outputting some debug information: {jsonResponse}')

        return whoIsLive
