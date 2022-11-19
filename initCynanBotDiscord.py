import asyncio

from authRepository import AuthRepository
from CynanBotCommon.networkClientProvider import NetworkClientProvider
from CynanBotCommon.storage.backingDatabase import BackingDatabase
from CynanBotCommon.storage.backingPsqlDatabase import BackingPsqlDatabase
from CynanBotCommon.storage.backingSqliteDatabase import BackingSqliteDatabase
from CynanBotCommon.storage.databaseType import DatabaseType
from CynanBotCommon.storage.psqlCredentialsProvider import \
    PsqlCredentialsProvider
from CynanBotCommon.timber.timber import Timber
from CynanBotCommon.twitch.twitchTokensRepository import TwitchTokensRepository
from cynanBotDiscord import CynanBotDiscord
from generalSettingsRepository import GeneralSettingsRepository
from twitchAnnounceChannelsRepository import TwitchAnnounceChannelsRepository
from twitchAnnounceSettingsRepository import TwitchAnnounceSettingsRepository
from twitchLiveHelper import TwitchLiveHelper
from twitchLiveUsersRepository import TwitchLiveUsersRepository
from usersRepository import UsersRepository

eventLoop = asyncio.get_event_loop()
timber = Timber(
    eventLoop = eventLoop
)
authHelper = AuthRepository()
generalSettingsRepository = GeneralSettingsRepository()

backingDatabase: BackingDatabase = None
if generalSettingsRepository.getAll().requireDatabaseType() == DatabaseType.POSTGRESQL:
    backingDatabase = BackingPsqlDatabase(
        eventLoop = eventLoop,
        psqlCredentialsProvider = PsqlCredentialsProvider()
    )
elif generalSettingsRepository.getAll().requireDatabaseType() == DatabaseType.SQLITE:
    backingDatabase = BackingSqliteDatabase(
        eventLoop = eventLoop
    )
else:
    raise RuntimeError(f'Unknown/misconfigured database type: \"{generalSettingsRepository.getAll().requireDatabaseType()}\"')

usersRepository = UsersRepository(
    backingDatabase = backingDatabase
)
twitchAnnounceChannelsRepository = TwitchAnnounceChannelsRepository(
    backingDatabase = backingDatabase,
    usersRepository = usersRepository
)
twitchAnnounceSettingsRepository = TwitchAnnounceSettingsRepository()
networkClientProvider = NetworkClientProvider(
    eventLoop = eventLoop
)

cynanBotDiscord = CynanBotDiscord(
    authRepository = authHelper,
    generalSettingsRepository = generalSettingsRepository,
    timber = timber,
    twitchAnnounceChannelsRepository = twitchAnnounceChannelsRepository,
    twitchAnnounceSettingsRepository = twitchAnnounceSettingsRepository,
    twitchLiveUsersRepository = TwitchLiveUsersRepository(
        twitchAnnounceChannelsRepository = twitchAnnounceChannelsRepository,
        twitchAnnounceSettingsRepository = twitchAnnounceSettingsRepository,
        twitchLiveHelper = TwitchLiveHelper(
            networkClientProvider = networkClientProvider,
            twitchClientId = authHelper.requireTwitchClientId(),
            twitchClientSecret = authHelper.requireTwitchClientSecret(),
            timber = timber,
            twitchTokensRepository = TwitchTokensRepository(
                networkClientProvider = networkClientProvider,
                timber = timber
            )
        ),
        usersRepository = usersRepository
    )
)


###################################################################################################
# begin CynanBotDiscord Commands                                                                  #
# More information on Discord bot commands available here:                                        #
# https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html                           #
#                                                                                                 #
# I hate putting the commands here like this, but I haven't found a way to have them completely   #
# isolated within the CynanBotDiscord class :( Maybe someday when I've learned more about Python. #
###################################################################################################

@cynanBotDiscord.command()
async def addTwitchUser(ctx, *args):
    await cynanBotDiscord.addTwitchUser(ctx)

@cynanBotDiscord.command()
async def listTwitchUsers(ctx, *args):
    await cynanBotDiscord.listTwitchUsers(ctx)

@cynanBotDiscord.command()
async def removeTwitchUser(ctx, *args):
    await cynanBotDiscord.removeTwitchUser(ctx)

###################################################################################################
# end CynanBotDiscord commands                                                                    #
###################################################################################################


timber.log('initCynanBotDiscord', 'Starting CynanBotDiscord...')
cynanBotDiscord.run(authHelper.requireDiscordToken())
