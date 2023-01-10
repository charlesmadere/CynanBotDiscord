from datetime import datetime
from typing import List, Optional

import CynanBotCommon.utils as utils
from CynanBotCommon.simpleDateTime import SimpleDateTime
from CynanBotCommon.storage.backingDatabase import BackingDatabase
from CynanBotCommon.storage.databaseConnection import DatabaseConnection
from CynanBotCommon.storage.databaseType import DatabaseType
from CynanBotCommon.users.usersRepositoryInterface import \
    UsersRepositoryInterface
from user import User


class UsersRepository(UsersRepositoryInterface):

    def __init__(self, backingDatabase: BackingDatabase):
        if not isinstance(backingDatabase, BackingDatabase):
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
                    INSERT INTO users (discorddiscriminator, discordid, discordname, mostrecentstreamdatetime, twitchname)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT(discordid) DO UPDATE SET discorddiscriminator = EXCLUDED.discorddiscriminator, discordname = EXCLUDED.discordname, mostrecentstreamdatetime = EXCLUDED.mostrecentstreamdatetime, twitchname = EXCLUDED.twitchname
                ''',
                user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getMostRecentStreamDateTime().getIsoFormatStr(), user.getTwitchName()
            )
        elif user.hasMostRecentStreamDateTime():
            await connection.execute(
                '''
                    INSERT INTO users (discorddiscriminator, discordid, discordname, mostrecentstreamdatetime)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT(discordid) DO UPDATE SET discorddiscriminator = EXCLUDED.discorddiscriminator, discordname = EXCLUDED.discordname, mostrecentstreamdatetime = EXCLUDED.mostrecentstreamdatetime
                ''',
                user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getMostRecentStreamDateTime().getIsoFormatStr()
            )
        elif user.hasTwitchName():
            await connection.execute(
                '''
                    INSERT INTO users (discorddiscriminator, discordid, discordname, twitchname)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT(discordid) DO UPDATE SET discorddiscriminator = EXCLUDED.discorddiscriminator, discordname = EXCLUDED.discordname, twitchname = EXCLUDED.twitchname
                ''',
                user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getTwitchName()
            )
        else:
            await connection.execute(
                '''
                    INSERT INTO users (discorddiscriminator, discordid, discordname)
                    VALUES ($1, $2, $3)
                    ON CONFLICT(discordid) DO UPDATE SET discorddiscriminator = EXCLUDED.discorddiscriminator, discordname = EXCLUDED.discordname
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
                SELECT discorddiscriminator, discordid, discordname, mostrecentstreamdatetime, twitchname FROM users
                WHERE discordid = $1
                LIMIT 1
            ''',
            discordId
        )

        if not utils.hasItems(row):
            await connection.close()
            raise ValueError(f'Unable to find user with discordId: \"{discordId}\"')

        mostRecentStreamDateTime: Optional[datetime] = utils.getDateTimeFromStr(row[3])
        mostRecentStreamSimpleDateTime: Optional[SimpleDateTime] = None
        if mostRecentStreamDateTime is not None:
            mostRecentStreamSimpleDateTime = SimpleDateTime(
                now = mostRecentStreamDateTime
            )

        user = User(
            discordDiscriminator = row[0],
            discordId = row[1],
            discordName = row[2],
            mostRecentStreamDateTime = mostRecentStreamSimpleDateTime,
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

        if connection.getDatabaseType() is DatabaseType.POSTGRESQL:
            await connection.createTableIfNotExists(
                '''
                    CREATE TABLE IF NOT EXISTS users (
                        discorddiscriminator public.citext NOT NULL,
                        discordid public.citext NOT NULL PRIMARY KEY,
                        discordname public.citext NOT NULL,
                        mostrecentstreamdatetime text DEFAULT NULL,
                        twitchname public.citext DEFAULT NULLE
                    )
                '''
            )
        elif connection.getDatabaseType() is DatabaseType.SQLITE:
            await connection.createTableIfNotExists(
                '''
                    CREATE TABLE IF NOT EXISTS users (
                        discorddiscriminator TEXT NOT NULL COLLATE NOCASE,
                        discordid TEXT NOT NULL PRIMARY KEY COLLATE NOCASE,
                        discordname TEXT NOT NULL COLLATE NOCASE,
                        mostrecentstreamdatetime TEXT DEFAULT NULL COLLATE NOCASE,
                        twitchname TEXT DEFAULT NULL COLLATE NOCASE
                    )
                '''
            )
        else:
            raise RuntimeError(f'unknown DatabaseType: \"{connection.getDatabaseType()}\"')

        await connection.close()
