from sqlite3 import OperationalError
from typing import Any, List, Optional

import CynanBotCommon.utils as utils
from CynanBotCommon.storage.backingDatabase import BackingDatabase
from CynanBotCommon.storage.databaseConnection import DatabaseConnection
from CynanBotCommon.storage.databaseType import DatabaseType
from user import User
from usersRepository import UsersRepository


class TwitchAnnounceChannel():

    def __init__(
        self,
        discordChannelId: int,
        users: Optional[List[User]] = None
    ):
        if not utils.isValidInt(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')
        elif discordChannelId < 0 or discordChannelId > utils.getLongMaxSafeSize():
            raise ValueError(f'discordChannelId argument is out of bounds: {discordChannelId}')

        self.__discordChannelId: int = discordChannelId
        self.__users: Optional[List[User]] = users

    def getDiscordChannelId(self) -> int:
        return self.__discordChannelId

    def getUsers(self) -> Optional[List[User]]:
        return self.__users

    def hasUsers(self) -> bool:
        return utils.hasItems(self.__users)


class TwitchAnnounceChannelsRepository():

    def __init__(
        self,
        backingDatabase: BackingDatabase,
        usersRepository: UsersRepository
    ):
        if not isinstance(backingDatabase, BackingDatabase):
            raise ValueError(f'backingDatabase argument is malformed: \"{backingDatabase}\"')
        elif not isinstance(usersRepository, UsersRepository):
            raise ValueError(f'usersRepository argument is malformed: \"{usersRepository}\"')

        self.__backingDatabase: BackingDatabase = backingDatabase
        self.__usersRepository: UsersRepository = usersRepository

        self.__isDatabaseReady: bool = False

    async def addUser(self, user: User, discordChannelId: int):
        if not isinstance(user, User):
            raise ValueError(f'user argument is malformed: \"{user}\"')
        elif not utils.isValidInt(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')
        elif discordChannelId < 0 or discordChannelId > utils.getLongMaxSafeSize():
            raise ValueError(f'discordChannelId argument is out of bounds: {discordChannelId}')

        await self.__createTablesForDiscordChannelId(discordChannelId)
        await self.__usersRepository.addOrUpdateUser(user)

        connection = await self.__getDatabaseConnection()
        await connection.execute(
            f'''
                INSERT INTO twitchannouncechannel_{discordChannelId} (discorduserid)
                VALUES ($1)
                ON CONFLICT (discorduserid) DO NOTHING
            ''',
            user.getDiscordId()
        )

        await connection.close()

    async def __createTablesForDiscordChannelId(self, discordChannelId: int):
        if not utils.isValidInt(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')
        elif discordChannelId < 0 or discordChannelId > utils.getLongMaxSafeSize():
            raise ValueError(f'discordChannelId argument is out of bounds: {discordChannelId}')

        connection = await self.__getDatabaseConnection()
        await connection.execute(
            '''
                INSERT INTO twitchannouncechannels (discordchannelid)
                VALUES ($1)
                ON CONFLICT (discordchannelid) DO NOTHING
            ''',
            str(discordChannelId)
        )

        if connection.getDatabaseType() is DatabaseType.POSTGRESQL:
            await connection.createTableIfNotExists(
                f'''
                    CREATE TABLE IF NOT EXISTS twitchannouncechannel_{discordChannelId} (
                        discorduserid public.citext NOT NULL PRIMARY KEY
                    )
                '''
            )
        elif connection.getDatabaseType() is DatabaseType.SQLITE:
            await connection.createTableIfNotExists(
                f'''
                    CREATE TABLE IF NOT EXISTS twitchannouncechannel_{discordChannelId} (
                        discorduserid TEXT NOT NULL PRIMARY KEY COLLATE NOCASE
                    )
                '''
            )
        else:
            raise RuntimeError(f'unknown DatabaseType: \"{connection.getDatabaseType()}\"')

        await connection.close()

    async def fetchTwitchAnnounceChannel(self, discordChannelId: int) ->  TwitchAnnounceChannel:
        if not utils.isValidInt(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')
        elif discordChannelId < 0 or discordChannelId > utils.getLongMaxSafeSize():
            raise ValueError(f'discordChannelId argument is out of bounds: {discordChannelId}')

        connection = await self.__getDatabaseConnection()
        rows: Optional[List[List[Any]]] = None

        try:
            rows = await connection.fetchRows(f'SELECT discorduserid FROM twitchannouncechannel_{discordChannelId}')
        except OperationalError:
            # this error can be safely ignored, it just means the above table doesn't exist
            pass

        if not utils.hasItems(rows):
            await connection.close()
            return TwitchAnnounceChannel(discordChannelId = discordChannelId)

        users: List[User] = list()

        for row in rows:
            user = await self.__usersRepository.getUserAsync(row[0])

            if not user.hasTwitchName():
                raise RuntimeError(f'Twitch announce user {user.getDiscordNameAndDiscriminator()} for channel {discordChannelId} has no Twitch name!')

            users.append(user)

        await connection.close()
        users.sort(key = lambda user: user.getDiscordName().lower())

        return TwitchAnnounceChannel(
            discordChannelId = discordChannelId,
            users = users
        )

    async def fetchTwitchAnnounceChannels(self) -> Optional[List[TwitchAnnounceChannel]]:
        connection = await self.__getDatabaseConnection()
        rows = await connection.fetchRows('SELECT discordchannelid FROM twitchannouncechannels')

        if not utils.hasItems(rows):
            await connection.close()
            return None

        twitchAnnounceChannels: List[TwitchAnnounceChannel] = list()

        for row in rows:
            twitchAnnounceChannel = await self.fetchTwitchAnnounceChannel(int(row[0]))
            twitchAnnounceChannels.append(twitchAnnounceChannel)

        await connection.close()
        return twitchAnnounceChannels

    async def __getDatabaseConnection(self) -> DatabaseConnection:
        await self.__initDatabaseTable()
        return await self.__backingDatabase.getConnection()

    async def __initDatabaseTable(self):
        if self.__isDatabaseReady:
            return

        self.__isDatabaseReady = True

        connection = await self.__backingDatabase.getConnection()

        if connection.getDatabaseType() is DatabaseType.POSTGRESQL:
            await connection.createTableIfNotExists(
                '''
                    CREATE TABLE IF NOT EXISTS twitchannouncechannels (
                        discordchannelid public.citext NOT NULL PRIMARY KEY
                    )
                '''
            )
        elif connection.getDatabaseType() is DatabaseType.SQLITE:
            await connection.createTableIfNotExists(
                '''
                    CREATE TABLE IF NOT EXISTS twitchannouncechannels (
                        discordchannelid TEXT NOT NULL PRIMARY KEY COLLATE NOCASE
                    )
                '''
            )
        else:
            raise RuntimeError(f'unknown DatabaseType: \"{connection.getDatabaseType()}\"')

        await connection.close()

    async def removeUser(self, user: User, discordChannelId: int):
        if not isinstance(user, User):
            raise ValueError(f'user argument is malformed: \"{user}\"')
        elif not utils.isValidInt(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')
        elif discordChannelId < 0 or discordChannelId > utils.getLongMaxSafeSize():
            raise ValueError(f'discordChannelId argument is out of bounds: {discordChannelId}')

        connection = await self.__getDatabaseConnection()

        try:
            connection.execute(
                f'''
                    DELETE FROM twitchannouncechannel_{discordChannelId}
                    WHERE discorduserid = $1
                ''',
                user.getDiscordId()
            )
        except OperationalError:
            # this error can be safely ignored, it just means the above table doesn't exist
            pass

        await connection.close()
