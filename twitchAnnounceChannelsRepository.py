from typing import List

import CynanBotCommon.utils as utils
from CynanBotCommon.backingDatabase import BackingDatabase
from user import User
from usersRepository import UsersRepository


class TwitchAnnounceChannel():

    def __init__(
        self,
        discordChannelId: int,
        users: List[User] = None
    ):
        if not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        self.__discordChannelId = discordChannelId
        self.__users = users

    def getDiscordChannelId(self) -> int:
        return self.__discordChannelId

    def getUsers(self) -> List[User]:
        return self.__users

    def hasUsers(self) -> bool:
        return utils.hasItems(self.__users)


class TwitchAnnounceChannelsRepository():

    def __init__(self, backingDatabase: BackingDatabase, usersRepository: UsersRepository):
        if backingDatabase is None:
            raise ValueError(f'backingDatabase argument is malformed: \"{backingDatabase}\"')
        elif usersRepository is None:
            raise ValueError(f'usersRepository argument is malformed: \"{usersRepository}\"')

        self.__backingDatabase = backingDatabase
        self.__usersRepository = usersRepository

    def addUser(self, user: User, discordChannelId: int):
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')
        elif not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        self.__usersRepository.addOrUpdateUser(user)

        connection = self.__backingDatabase.getConnection()
        connection.execute(
            f'''
                CREATE TABLE IF NOT EXISTS twitchAnnounceChannel_{discordChannelId} (
                    discordUserId TEXT NOT NULL COLLATE NOCASE
                )
            '''
        )

        connection.commit()

        cursor = self.__backingDatabase.getConnection().cursor()
        cursor.execute(
            f'''
                INSERT INTO twitchAnnounceChannel_{discordChannelId} (discordUserId)
                VALUES (?)
                ON CONFLICT(discordUserId) ABORT
            ''',
            ( user.getDiscordId(), )
        )

        cursor.close()

    def getTwitchAnnounceChannel(self, discordChannelId: int) ->  TwitchAnnounceChannel:
        if not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        cursor = self.__backingDatabase.getConnection().cursor()
        cursor.execute(f'SELECT discordUserId FROM twitchAnnounceChannel_{discordChannelId}')
        rows = cursor.fetchall()

        if not utils.hasItems(rows):
            cursor.close()
            return TwitchAnnounceChannel(discordChannelId = discordChannelId)

        users = list()

        for row in rows:
            user = self.__usersRepository.fetchUser(row[0])
            users.append(user)
            cursor.close()

        return TwitchAnnounceChannel(
            discordChannelId = discordChannelId,
            users = users
        )
