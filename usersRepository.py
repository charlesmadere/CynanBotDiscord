import CynanBotCommon.utils as utils
from CynanBotCommon.backingDatabase import BackingDatabase
from user import User


class UsersRepository():

    def __init__(self, backingDatabase: BackingDatabase):
        if backingDatabase is None:
            raise ValueError(f'backingDatabase argument is malformed: \"{backingDatabase}\"')

        self.__backingDatabase = backingDatabase

        connection = backingDatabase.getConnection()
        connection.execute(
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
        connection.commit()

    def addOrUpdateUser(self, user: User):
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')

        connection = self.__backingDatabase.getConnection()
        cursor = connection.cursor()

        if user.hasMostRecentStreamDateTime() and user.hasTwitchName():
            cursor.execute(
                '''
                    INSERT INTO users (discordDiscriminator, discordId, discordName, mostRecentStreamDateTime, twitchName)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(discordId) DO UPDATE SET discordDiscriminator = excluded.discordDiscriminator, discordName = excluded.discordName, mostRecentStreamDateTime = excluded.mostRecentStreamDateTime, twitchName = excluded.twitchName
                ''',
                ( user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getMostRecentStreamDateTimeStr(), user.getTwitchName() )
            )
        elif user.hasMostRecentStreamDateTime():
            cursor.execute(
                '''
                    INSERT INTO users (discordDiscriminator, discordId, discordName, mostRecentStreamDateTime)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(discordId) DO UPDATE SET discordDiscriminator = excluded.discordDiscriminator, discordName = excluded.discordName, mostRecentStreamDateTime = excluded.mostRecentStreamDateTime
                ''',
                ( user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getMostRecentStreamDateTimeStr() )
            )
        elif user.hasTwitchName():
            cursor.execute(
                '''
                    INSERT INTO users (discordDiscriminator, discordId, discordName, twitchName)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(discordId) DO UPDATE SET discordDiscriminator = excluded.discordDiscriminator, discordName = excluded.discordName, twitchName = excluded.twitchName
                ''',
                ( user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName(), user.getTwitchName() )
            )
        else:
            cursor.execute(
                '''
                    INSERT INTO users (discordDiscriminator, discordId, discordName)
                    VALUES (?, ?, ?)
                    ON CONFLICT(discordId) DO UPDATE SET discordDiscriminator = excluded.discordDiscriminator, discordName = excluded.discordName
                ''',
                ( user.getDiscordDiscriminator(), user.getDiscordId(), user.getDiscordName() )
            )

        connection.commit()
        cursor.close()

    def fetchUser(self, discordId: str) -> User:
        if not utils.isValidStr(discordId):
            raise ValueError(f'discordId argument is malformed: {discordId}')

        cursor = self.__backingDatabase.getConnection().cursor()
        cursor.execute(
            '''
                SELECT discordDiscriminator, discordId, discordName, mostRecentStreamDateTime, twitchName FROM users 
                WHERE discordId = ?
            ''',
            ( discordId, )
        )

        row = cursor.fetchone()

        if row is None:
            cursor.close()
            raise ValueError(f'Unable to find user with discordId: \"{discordId}\"')

        user = User(
            discordDiscriminator = row[0],
            discordId = row[1],
            discordName = row[2],
            mostRecentStreamDateTime = utils.getDateTimeFromStr(row[3]),
            twitchName = row[4]
        )

        cursor.close()
        return user
