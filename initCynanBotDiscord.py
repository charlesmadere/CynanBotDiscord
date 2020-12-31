import os
import sched
import time
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
scheduler = sched.scheduler(time.time, time.sleep)

cynanBotDiscord = CynanBotDiscord(
    analogueSettingsHelper=analogueSettingsHelper,
    analogueStoreRepository=analogueStoreRepository,
    scheduler=scheduler
)

print('Starting CynanBotDiscord...')
cynanBotDiscord.run(discordAuthHelper.getToken())
