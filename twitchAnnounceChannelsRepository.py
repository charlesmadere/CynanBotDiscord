from sqlite3 import OperationalError
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

        connection = self.__backingDatabase.getConnection()
        connection.execute(
            '''
                CREATE TABLE IF NOT EXISTS twitchAnnounceChannels (
                    discordChannelId TEXT NOT NULL UNIQUE COLLATE NOCASE
                )
            '''
        )
        connection.commit()

    def addUser(self, user: User, discordChannelId: int):
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')
        elif not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        self.__usersRepository.addOrUpdateUser(user)

        connection = self.__backingDatabase.getConnection()
        cursor = connection.cursor()
        cursor.execute(
            '''
                INSERT INTO twitchAnnounceChannels (discordChannelId)
                VALUES (?)
                ON CONFLICT IGNORE
            ''',
            ( str(discordChannelId), )
        )
        connection.commit()
        cursor.close()

        connection = self.__backingDatabase.getConnection()
        connection.execute(
            f'''
                CREATE TABLE IF NOT EXISTS twitchAnnounceChannel_{discordChannelId} (
                    discordUserId TEXT NOT NULL UNIQUE COLLATE NOCASE
                )
            '''
        )
        connection.commit()

        cursor = connection.cursor()
        cursor.execute(
            f'''
                INSERT INTO twitchAnnounceChannel_{discordChannelId} (discordUserId)
                VALUES (?)
                ON CONFLICT IGNORE
            ''',
            ( str(user.getDiscordId()), )
        )
        connection.commit()
        cursor.close()

    def fetchTwitchAnnounceChannel(self, discordChannelId: int) ->  TwitchAnnounceChannel:
        if not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        cursor = self.__backingDatabase.getConnection().cursor()

        try:
            cursor.execute(f'SELECT discordUserId FROM twitchAnnounceChannel_{discordChannelId}')
        except OperationalError:
            return None

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

    def fetchTwitchAnnounceChannels(self) -> List[TwitchAnnounceChannel]:
        cursor = self.__backingDatabase.getConnection().cursor()
        cursor.execute(f'SELECT discordChannelId FROM twitchAnnounceChannels')
        rows = cursor.fetchall()

        if not utils.hasItems(rows):
            cursor.close()
            return None

        twitchAnnounceChannels = list()

        for row in rows:
            twitchAnnounceChannel = self.fetchTwitchAnnounceChannel(row[0])
            twitchAnnounceChannels.append(twitchAnnounceChannel)

        return twitchAnnounceChannel

    def removeUser(self, user: User, discordChannelId: int):
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')
        elif not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        connection = self.__backingDatabase.getConnection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                f'''
                    DELETE FROM twitchAnnounceChannel_{discordChannelId}
                    WHERE discordUserId = ?
                ''',
                ( str(user.getDiscordId()), )
            )
        except OperationalError:
            pass

        connection.commit()
        cursor.close()
