from datetime import timedelta

from analogueAnnounceChannelsRepository import AnalogueAnnounceChannelsRepository
from analogueSettingsHelper import AnalogueSettingsHelper
from authHelper import AuthHelper
from CynanBotCommon.analogueStoreRepository import AnalogueStoreRepository
from CynanBotCommon.backingDatabase import BackingDatabase
from CynanBotCommon.twitchTokensRepository import TwitchTokensRepository
from cynanBotDiscord import CynanBotDiscord
from generalSettingsHelper import GeneralSettingsHelper
from twitchAnnounceChannelsRepository import TwitchAnnounceChannelsRepository
from twitchAnnounceSettingsHelper import TwitchAnnounceSettingsHelper
from twitchLiveHelper import TwitchLiveHelper
from twitchLiveUsersRepository import TwitchLiveUsersRepository
from usersRepository import UsersRepository


analogueSettingsHelper = AnalogueSettingsHelper()
authHelper = AuthHelper()
backingDatabase = BackingDatabase()
usersRepository = UsersRepository(
    backingDatabase = backingDatabase
)
twitchAnnounceChannelsRepository = TwitchAnnounceChannelsRepository(
    backingDatabase = backingDatabase,
    usersRepository = usersRepository
)
twitchAnnounceSettingsHelper = TwitchAnnounceSettingsHelper()

cynanBotDiscord = CynanBotDiscord(
    analogueAnnounceChannelsRepository = AnalogueAnnounceChannelsRepository(
        backingDatabase = backingDatabase,
        usersRepository = usersRepository
    ),
    analogueSettingsHelper = analogueSettingsHelper,
    analogueStoreRepository = AnalogueStoreRepository(
        cacheTimeDelta = timedelta(seconds = analogueSettingsHelper.getAnalogueStoreCacheSeconds())
    ),
    authHelper = authHelper,
    generalSettingsHelper = GeneralSettingsHelper(),
    twitchAnnounceChannelsRepository = twitchAnnounceChannelsRepository,
    twitchAnnounceSettingsHelper = twitchAnnounceSettingsHelper,
    twitchLiveUsersRepository = TwitchLiveUsersRepository(
        twitchAnnounceChannelsRepository = twitchAnnounceChannelsRepository,
        twitchAnnounceSettingsHelper = twitchAnnounceSettingsHelper,
        twitchLiveHelper = TwitchLiveHelper(
            twitchClientId = authHelper.getTwitchClientId(),
            twitchClientSecret = authHelper.getTwitchClientSecret(),
            twitchTokensRepository = TwitchTokensRepository()
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
async def addAnaloguePriorityProduct(ctx, *args):
    await cynanBotDiscord.addAnaloguePriorityProduct(ctx)

@cynanBotDiscord.command()
async def addAnalogueUser(ctx, *args):
    await cynanBotDiscord.addAnalogueUser(ctx)

@cynanBotDiscord.command()
async def addTwitchUser(ctx, *args):
    await cynanBotDiscord.addTwitchUser(ctx)

@cynanBotDiscord.command()
async def listAnaloguePriorityProducts(ctx, *args):
    await cynanBotDiscord.listAnaloguePriorityProducts(ctx)

@cynanBotDiscord.command()
async def listAnalogueUsers(ctx, *args):
    await cynanBotDiscord.listAnalogueUsers(ctx)

@cynanBotDiscord.command()
async def listTwitchUsers(ctx, *args):
    await cynanBotDiscord.listTwitchUsers(ctx)

@cynanBotDiscord.command()
async def removeAnaloguePriorityProduct(ctx, *args):
    await cynanBotDiscord.removeAnaloguePriorityProduct(ctx)

@cynanBotDiscord.command()
async def removeAnalogueUser(ctx, *args):
    await cynanBotDiscord.removeAnalogueUser(ctx)

@cynanBotDiscord.command()
async def removeTwitchUser(ctx, *args):
    await cynanBotDiscord.removeTwitchUser(ctx)

###################################################################################################
# end CynanBotDiscord commands                                                                    #
###################################################################################################


print('Starting CynanBotDiscord...')
cynanBotDiscord.run(authHelper.getDiscordToken())
