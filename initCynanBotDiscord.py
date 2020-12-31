import os

import discord

from CynanBotCommon.analogueStoreRepository import AnalogueStoreRepository
from cynanBotDiscord import CynanBotDiscord
from discordAuthHelper import DiscordAuthHelper

analogueStoreRepository = AnalogueStoreRepository()
discordAuthHelper = DiscordAuthHelper()

cynanBotDiscord = CynanBotDiscord(
    analogueStoreRepository=analogueStoreRepository
)

print('Starting CynanBotDiscord...')
cynanBotDiscord.run(discordAuthHelper.getToken())
