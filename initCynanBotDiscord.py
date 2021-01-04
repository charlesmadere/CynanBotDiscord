import os
from datetime import timedelta

import discord

from analogueSettingsHelper import AnalogueSettingsHelper
from CynanBotCommon.analogueStoreRepository import AnalogueStoreRepository
from cynanBotDiscord import CynanBotDiscord
from discordAuthHelper import DiscordAuthHelper


analogueSettingsHelper = AnalogueSettingsHelper()
analogueStoreRepository = AnalogueStoreRepository(
    cacheTimeDelta=timedelta(seconds=30)
)
discordAuthHelper = DiscordAuthHelper()

cynanBotDiscord = CynanBotDiscord(
    analogueSettingsHelper=analogueSettingsHelper,
    analogueStoreRepository=analogueStoreRepository
)

print('Starting CynanBotDiscord...')
cynanBotDiscord.run(discordAuthHelper.getToken())
