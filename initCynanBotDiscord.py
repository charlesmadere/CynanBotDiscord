from datetime import timedelta

from analogueSettingsHelper import AnalogueSettingsHelper
from authHelper import AuthHelper
from CynanBotCommon.analogueStoreRepository import AnalogueStoreRepository
from cynanBotDiscord import CynanBotDiscord
from generalSettingsHelper import GeneralSettingsHelper
from twitchAccounceSettingsHelper import TwitchAnnounceSettingsHelper
from twitchLiveHelper import TwitchLiveHelper
from twitchTokensRepository import TwitchTokensRepository


analogueSettingsHelper = AnalogueSettingsHelper()
authHelper = AuthHelper()

cynanBotDiscord = CynanBotDiscord(
    analogueSettingsHelper = AnalogueSettingsHelper(),
    analogueStoreRepository = AnalogueStoreRepository(
        cacheTimeDelta = timedelta(seconds = analogueSettingsHelper.getAnalogueStoreCacheSeconds())
    ),
    authHelper = authHelper,
    generalSettingsHelper = GeneralSettingsHelper(),
    twitchAnnounceSettingsHelper = TwitchAnnounceSettingsHelper(),
    twitchLiveHelper = TwitchLiveHelper(
        clientId = authHelper.getTwitchClientId(),
        clientSecret = authHelper.getTwitchClientSecret(),
        twitchTokensRepository = TwitchTokensRepository()
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
async def addAnalogueUser(ctx, *args):
    await cynanBotDiscord.addAnalogueUser(ctx)

@cynanBotDiscord.command()
async def addTwitchUser(ctx, *args):
    await cynanBotDiscord.addTwitchUser(ctx)

@cynanBotDiscord.command()
async def analogue(ctx, *args):
    await cynanBotDiscord.analogue(ctx)

@cynanBotDiscord.command()
async def listAnalogueUsers(ctx, *args):
    await cynanBotDiscord.listAnalogueUsers(ctx)

@cynanBotDiscord.command()
async def listPriorityProducts(ctx, *args):
    await cynanBotDiscord.listPriorityProducts(ctx)

@cynanBotDiscord.command()
async def listTwitchUsers(ctx, *args):
    await cynanBotDiscord.listTwitchUsers(ctx)

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
