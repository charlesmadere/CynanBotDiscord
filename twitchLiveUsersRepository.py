from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import CynanBotCommon.utils as utils
from twitchAnnounceChannelsRepository import TwitchAnnounceChannelsRepository
from twitchAnnounceSettingsHelper import TwitchAnnounceSettingsHelper
from twitchLiveHelper import TwitchLiveData, TwitchLiveHelper
from user import User
from usersRepository import UsersRepository


class TwitchLiveUserData():

    def __init__(
        self,
        discordChannelIds: List[int],
        twitchLiveData: TwitchLiveData,
        user: User
    ):
        if not utils.hasItems(discordChannelIds):
            raise ValueError(f'discordChannelIds argument is malformed: \"{discordChannelIds}\"')
        elif twitchLiveData is None:
            raise ValueError(f'twitchLiveData argument is malformed: \"{twitchLiveData}\"')
        elif user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')

        self.__discordChannelIds: List[int] = discordChannelIds
        self.__twitchLiveData: TwitchLiveData = twitchLiveData
        self.__user: User = user

    def getDiscordChannelIds(self) -> List[int]:
        return self.__discordChannelIds

    def getTwitchLiveData(self) -> TwitchLiveData:
        return self.__twitchLiveData

    def getUser(self) -> User:
        return self.__user


class TwitchLiveUsersRepository():

    def __init__(
        self,
        twitchAnnounceChannelsRepository: TwitchAnnounceChannelsRepository,
        twitchAnnounceSettingsHelper: TwitchAnnounceSettingsHelper,
        twitchLiveHelper: TwitchLiveHelper,
        usersRepository: UsersRepository
    ):
        if twitchAnnounceChannelsRepository is None:
            raise ValueError(f'twitchAnnounceChannelsRepository argument is malformed: \"{twitchAnnounceChannelsRepository}\"')
        elif twitchAnnounceSettingsHelper is None:
            raise ValueError(f'twitchAnnounceSettingsHelper argument is malformed: \"{twitchAnnounceSettingsHelper}\"')
        elif twitchLiveHelper is None:
            raise ValueError(f'twitchLiveHelper argument is malformed: \"{twitchLiveHelper}\"')
        elif usersRepository is None:
            raise ValueError(f'usersRepository argument is malformed: \"{usersRepository}\"')

        self.__twitchAnnounceChannelsRepository: TwitchAnnounceChannelsRepository = twitchAnnounceChannelsRepository
        self.__twitchAnnounceSettingsHelper: TwitchAnnounceSettingsHelper = twitchAnnounceSettingsHelper
        self.__twitchLiveHelper: TwitchLiveHelper = twitchLiveHelper
        self.__usersRepository: UsersRepository = usersRepository

    async def fetchTwitchLiveUserData(self) -> List[TwitchLiveUserData]:
        twitchAnnounceChannels = await self.__twitchAnnounceChannelsRepository.fetchTwitchAnnounceChannels()
        if not utils.hasItems(twitchAnnounceChannels):
            return None

        now = datetime.utcnow()        
        userIdsToChannels: Dict[str, Set[int]] = dict()
        userIdsToUsers: Dict[str, User] = dict()

        for twitchAnnounceChannel in twitchAnnounceChannels:
            if twitchAnnounceChannel.hasUsers():
                for user in twitchAnnounceChannel.getUsers():
                    if user.getDiscordId() not in userIdsToChannels:
                        userIdsToChannels[user.getDiscordId()] = set()

                        if user.getDiscordId() not in userIdsToUsers:
                            userIdsToUsers[user.getDiscordId()] = user

                    userIdsToChannels[user.getDiscordId()].add(twitchAnnounceChannel.getDiscordChannelId())

        if not utils.hasItems(userIdsToChannels) or not utils.hasItems(userIdsToUsers):
            return None

        users: List[User] = list()
        for user in userIdsToUsers.values():
            users.append(user)

        whoIsLive: Optional[Dict[User, TwitchLiveData]] = None
        try:
            whoIsLive = await self.__twitchLiveHelper.fetchWhoIsLive(users)
        except (RuntimeError, ValueError):
            return None

        if not utils.hasItems(whoIsLive):
            return None

        announceTimeDelta = timedelta(minutes = self.__twitchAnnounceSettingsHelper.getAnnounceFalloffMinutes())
        removeTheseUsers: List[User] = list()

        for user in whoIsLive:
            if user.hasMostRecentStreamDateTime() and user.getMostRecentStreamDateTime() + announceTimeDelta >= now:
                removeTheseUsers.append(user)

            user.setMostRecentStreamDateTime(now)
            await self.__usersRepository.addOrUpdateUser(user)

        if utils.hasItems(removeTheseUsers):
            for removeThisUser in removeTheseUsers:
                del whoIsLive[removeThisUser]

        if not utils.hasItems(whoIsLive):
            return None

        twitchLiveUserDataList: List[TwitchLiveUserData] = list()
        for user, twitchLiveData in whoIsLive.items():
            twitchLiveUserDataList.append(TwitchLiveUserData(
                discordChannelIds = userIdsToChannels[user.getDiscordId()],
                twitchLiveData = twitchLiveData,
                user = user
            ))

        twitchLiveUserDataList.sort(key = lambda entry: entry.getTwitchLiveData().getUserLogin().lower())
        return twitchLiveUserDataList
