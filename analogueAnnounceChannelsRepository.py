from sqlite3 import OperationalError
from typing import List

import CynanBotCommon.utils as utils
from CynanBotCommon.analogueStoreRepository import AnalogueProductType
from CynanBotCommon.backingDatabase import BackingDatabase
from user import User
from usersRepository import UsersRepository


class AnalogueAnnounceChannel():

    def __init__(
        self,
        discordChannelId: int,
        analoguePriorityProducts: List[AnalogueProductType] = None,
        users: List[User] = None
    ):
        if not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        self.__discordChannelId = discordChannelId
        self.__analoguePriorityProducts = analoguePriorityProducts
        self.__users = users

    def getAnaloguePriorityProducts(self) -> List[AnalogueProductType]:
        return self.__analoguePriorityProducts

    def getDiscordChannelId(self) -> int:
        return self.__discordChannelId

    def getUsers(self) -> List[User]:
        return self.__users

    def hasAnaloguePriorityProducts(self) -> bool:
        return utils.hasItems(self.__analoguePriorityProducts)

    def hasUsers(self) -> bool:
        return utils.hasItems(self.__users)


class AnalogueAnnounceChannelsRepository():

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
                CREATE TABLE IF NOT EXISTS analogueAnnounceChannels (
                    discordChannelId TEXT NOT NULL UNIQUE COLLATE NOCASE
                )
            '''
        )
        connection.commit()

    def addAnaloguePriorityProduct(
        self,
        analoguePriorityProduct: AnalogueProductType,
        discordChannelId: int
    ):
        if analoguePriorityProduct is None:
            raise ValueError(f'analoguePriorityProduct argument is malformed: \"{analoguePriorityProduct}\"')
        elif not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        self.__createTablesForDiscordChannelId(discordChannelId)

        connection = self.__backingDatabase.getConnection()
        cursor = connection.cursor()
        cursor.execute(
            f'''
                INSERT INTO analogueAnnounceChannelProducts_{discordChannelId} (analoguePriorityProduct)
                VALUES (?)
                ON CONFLICT (analoguePriorityProduct) DO NOTHING
            ''',
            ( analoguePriorityProduct.toStr(), )
        )
        connection.commit()
        cursor.close()

    def addUser(self, user: User, discordChannelId: int):
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')
        elif not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        self.__createTablesForDiscordChannelId(discordChannelId)
        self.__usersRepository.addOrUpdateUser(user)

        connection = self.__backingDatabase.getConnection()
        cursor = connection.cursor()
        cursor.execute(
            f'''
                INSERT INTO analogueAnnounceChannelUsers_{discordChannelId} (discordUserId)
                VALUES (?)
                ON CONFLICT (discordUserId) DO NOTHING
            ''',
            ( user.getDiscordId(), )
        )
        connection.commit()
        cursor.close()

    def __createTablesForDiscordChannelId(self, discordChannelId: int):
        if not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        connection = self.__backingDatabase.getConnection()
        cursor = connection.cursor()
        cursor.execute(
            '''
                INSERT INTO analogueAnnounceChannels
                VALUES (?)
                ON CONFLICT (discordChannelId) DO NOTHING
            ''',
            ( str(discordChannelId), )
        )
        connection.commit()
        cursor.close()

        connection = self.__backingDatabase.getConnection()
        connection.execute(
            f'''
                CREATE TABLE IF NOT EXISTS analogueAnnounceChannelProducts_{discordChannelId} (
                    analoguePriorityProduct TEXT NOT NULL UNIQUE COLLATE NOCASE
                )
            '''
        )
        connection.commit()

        connection = self.__backingDatabase.getConnection()
        connection.execute(
            f'''
                CREATE TABLE IF NOT EXISTS analogueAnnounceChannelUsers_{discordChannelId} (
                    discordUserId TEXT NOT NULL UNIQUE COLLATE NOCASE
                )
            '''
        )
        connection.commit()

    def fetchAnalogueAnnounceChannel(self, discordChannelId: int) -> AnalogueAnnounceChannel:
        if not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        cursor = self.__backingDatabase.getConnection().cursor()
        rows = None

        try:
            cursor.execute(f'SELECT analoguePriorityProduct FROM analogueAnnounceChannelProducts_{discordChannelId}')
            rows = cursor.fetchall()
        except OperationalError:
            # this error can be safely ignored, it just means the above table doesn't exist
            pass

        analoguePriorityProducts = list()

        if utils.hasItems(rows):
            for row in rows:
                analoguePriorityProduct = AnalogueProductType.fromStr(row[0])
                analoguePriorityProducts.append(analoguePriorityProduct)

        cursor.close()
        cursor = self.__backingDatabase.getConnection().cursor()
        rows = None

        try:
            cursor.execute(f'SELECT discordUserId FROM analogueAnnounceChannelUsers_{discordChannelId}')
            rows = cursor.fetchall()
        except OperationalError:
            # this error can be safely ignored, it just means the above table doesn't exist
            pass

        users = list()

        if utils.hasItems(rows):
            for row in rows:
                user = self.__usersRepository.fetchUser(row[0])
                users.append(user)

        cursor.close()
        users.sort(key = lambda user: user.getDiscordName().lower())

        return AnalogueAnnounceChannel(
            discordChannelId = discordChannelId,
            analoguePriorityProducts = analoguePriorityProducts,
            users = users
        )

    def fetchAnalogueAnnounceChannels(self) -> List[AnalogueAnnounceChannel]:
        cursor = self.__backingDatabase.getConnection().cursor()
        cursor.execute(f'SELECT discordChannelId FROM analogueAnnounceChannels')
        rows = cursor.fetchall()

        if not utils.hasItems(rows):
            cursor.close()
            return None

        analogueAnnounceChannels = list()

        for row in rows:
            analogueAnnounceChannel = self.fetchAnalogueAnnounceChannel(int(row[0]))
            analogueAnnounceChannels.append(analogueAnnounceChannel)

        return analogueAnnounceChannels

    def removeAnaloguePriorityProduct(
        self,
        analoguePriorityProduct: AnalogueProductType,
        discordChannelId: int
    ):
        if analoguePriorityProduct is None:
            raise ValueError(f'analoguePriorityProduct argument is malformed: \"{analoguePriorityProduct}\"')
        elif not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        connection = self.__backingDatabase.getConnection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                f'''
                    DELETE FROM analogueAnnounceChannelProducts_{discordChannelId}
                    WHERE analoguePriorityProduct = ?
                ''',
                ( analoguePriorityProduct.name )
            )
        except OperationalError:
            # this error can be safely ignored, it just means the above table doesn't exist
            pass

        connection.commit()
        cursor.close()

    def removeUser(self, user: User, discordChannelId: int) -> bool:
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')
        elif not utils.isValidNum(discordChannelId):
            raise ValueError(f'discordChannelId argument is malformed: \"{discordChannelId}\"')

        connection = self.__backingDatabase.getConnection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                f'''
                    DELETE FROM analogueAnnounceChannelUsers_{discordChannelId}
                    WHERE discordUserId = ?
                ''',
                ( str(user.getDiscordId()), )
            )
        except OperationalError:
            # this error can be safely ignored, it just means the above table doesn't exist
            pass

        connection.commit()
        cursor.close()
