from typing import List

import CynanBotCommon.utils as utils
from CynanBotCommon.storage.backingDatabase import BackingDatabase
from CynanBotCommon.storage.databaseConnection import DatabaseConnection
from CynanBotCommon.users.usersRepositoryInterface import \
    UsersRepositoryInterface
from user import User


class UsersRepository(UsersRepositoryInterface):

    def __init__(self, backingDatabase: BackingDatabase):
        if backingDatabase is None:
            raise ValueError(f'backingDatabase argument is malformed: \"{backingDatabase}\"')

        self.__backingDatabase: BackingDatabase = backingDatabase

        self.__isDatabaseReady: bool = False

    async def addOrUpdateUser(self, user: User):
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')

        connection = await self.__getDatabaseConnection()

        if user.hasMostRecentStreamDateTime() and user.hasTwitchName():
            await connection.execute(
                '''
                    INSERT INTO users (discordDiscriminator, discordId, discordName, mostRecentStreamDateTime, twitchName)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT(discordId) DO UPDATE SET discordDiscriminator = excluded.discordDiscriminator, discordName = excluded.discordName, mostRecentStreamDateTime = excluded.mostRecentStreamDateTime, twitchName = excluded.twitchName
                ''',
                user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getMostRecentStreamDateTimeStr(), user.getTwitchName()
            )
        elif user.hasMostRecentStreamDateTime():
            await connection.execute(
                '''
                    INSERT INTO users (discordDiscriminator, discordId, discordName, mostRecentStreamDateTime)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT(discordId) DO UPDATE SET discordDiscriminator = excluded.discordDiscriminator, discordName = excluded.discordName, mostRecentStreamDateTime = excluded.mostRecentStreamDateTime
                ''',
                user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getMostRecentStreamDateTimeStr()
            )
        elif user.hasTwitchName():
            await connection.execute(
                '''
                    INSERT INTO users (discordDiscriminator, discordId, discordName, twitchName)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT(discordId) DO UPDATE SET discordDiscriminator = excluded.discordDiscriminator, discordName = excluded.discordName, twitchName = excluded.twitchName
                ''',
                user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getTwitchName()
            )
        else:
            await connection.execute(
                '''
                    INSERT INTO users (discordDiscriminator, discordId, discordName)
                    VALUES ($1, $2, $3)
                    ON CONFLICT(discordId) DO UPDATE SET discordDiscriminator = excluded.discordDiscriminator, discordName = excluded.discordName
                ''',
                user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName()
            )

        await connection.close()

    async def __getDatabaseConnection(self) -> DatabaseConnection:
        await self.__initDatabaseTable()
        return await self.__backingDatabase.getConnection()

    def getUser(self, handle: str) -> User:
        raise NotImplementedError()

    async def getUserAsync(self, discordId: str) -> User:
        if not utils.isValidStr(discordId):
            raise ValueError(f'discordId argument is malformed: {discordId}')

        connection = await self.__getDatabaseConnection()
        row = await connection.fetchRow(
            '''
                SELECT discordDiscriminator, discordId, discordName, mostRecentStreamDateTime, twitchName FROM users 
                WHERE discordId = $1
            ''',
            discordId
        )

        if not utils.hasItems(row):
            await connection.close()
            raise ValueError(f'Unable to find user with discordId: \"{discordId}\"')

        user = User(
            discordDiscriminator = row[0],
            discordId = row[1],
            discordName = row[2],
            mostRecentStreamDateTime = utils.getDateTimeFromStr(row[3]),
            twitchName = row[4]
        )

        await connection.close()
        return user

    def getUsers(self) -> List[User]:
        raise NotImplementedError()

    def getUsersAsync(self) -> List[User]:
        raise NotImplementedError()

    async def __initDatabaseTable(self):
        if self.__isDatabaseReady:
            return

        self.__isDatabaseReady = True

        connection = await self.__backingDatabase.getConnection()
        await connection.execute(
            '''
                CREATE TABLE IF NOT EXISTS users (
                    discordDiscriminator TEXT NOT NULL COLLATE NOCASE,
                    discordId TEXT NOT NULL UNIQUE PRIMARY KEY COLLATE NOCASE,
                    discordName TEXT NOT NULL COLLATE NOCASE,
                    mostRecentStreamDateTime TEXT DEFAULT NULL COLLATE NOCASE,
                    twitchName TEXT DEFAULT NULL COLLATE NOCASE
                )
            '''
        )

        await connection.close()
