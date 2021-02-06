from datetime import timedelta

from discord.ext import commands

from analogueSettingsHelper import AnalogueSettingsHelper
from CynanBotCommon.analogueStoreRepository import AnalogueStoreRepository
from cynanBotDiscord import CynanBotDiscord
from discordAuthHelper import DiscordAuthHelper


analogueSettingsHelper = AnalogueSettingsHelper()
analogueStoreRepository = AnalogueStoreRepository(
    cacheTimeDelta = timedelta(seconds=30)
)
discordAuthHelper = DiscordAuthHelper()

cynanBotDiscord = CynanBotDiscord(
    analogueSettingsHelper = analogueSettingsHelper,
    analogueStoreRepository = analogueStoreRepository
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
async def addUser(ctx, *args):
    await cynanBotDiscord.addUser(ctx)

@cynanBotDiscord.command()
async def analogue(ctx, *args):
    await cynanBotDiscord.analogue(ctx)

@cynanBotDiscord.command()
async def listPriorityProducts(ctx, *args):
    await cynanBotDiscord.listPriorityProducts(ctx)

@cynanBotDiscord.command()
async def listUsers(ctx, *args):
    await cynanBotDiscord.listUsers(ctx)

@cynanBotDiscord.command()
async def removeUser(ctx, *args):
    await cynanBotDiscord.removeUser(ctx)

###################################################################################################
# end CynanBotDiscord commands                                                                    #
###################################################################################################


print('Starting CynanBotDiscord...')
cynanBotDiscord.run(discordAuthHelper.getToken())
