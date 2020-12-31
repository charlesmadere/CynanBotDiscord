import os

import discord

from discordAuthHelper import DiscordAuthHelper


discordAuthHelper = DiscordAuthHelper()
discordClient = discord.client()

@discordClient.event
async def on_ready():
    print(f'{discordClient.user} has connected to Discord!')

discordClient.run(discordAuthHelper.getToken())
