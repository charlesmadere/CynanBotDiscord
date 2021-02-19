from usersRepository import UsersRepository
from CynanBotCommon.backingDatabase import BackingDatabase

class TwitchAnnounceChannelsRepository():

    def __init__(self, backingDatabase: BackingDatabase, usersRepository: UsersRepository):
        if backingDatabase is None:
            raise ValueError(f'backingDatabase argument is malformed: \"{backingDatabase}\"')
        elif usersRepository is None:
            raise ValueError(f'usersRepository argument is malformed: \"{usersRepository}\"')

        self.__backingDatabase = backingDatabase
        self.__usersRepository = usersRepository

        connection = backingDatabase.getConnection()
        connection.execute(
            '''
                CREATE TABLE IF NOT EXISTS twitchAnnounceChannels (
                    discordChannelId TEXT NOT NULL PRIMARY KEY COLLATE NOCASE
                )
            '''
        )
        
        connection.commit()
