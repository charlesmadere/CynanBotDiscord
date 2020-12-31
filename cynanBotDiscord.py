import discord

import CynanBotCommon.utils as utils
from CynanBotCommon.analogueStoreRepository import (AnalogueStoreProduct,
                                                    AnalogueStoreRepository,
                                                    AnalogueStoreStock)


class CynanBotDiscord(discord.Client):

    def __init__(
        self,
        analogueStoreRepository: AnalogueStoreRepository
    ):
        if analogueStoreRepository is None:
            raise ValueError(f'analogueStoreRepository argument is malformed: \"{analogueStoreRepository}\"')

        self.__analogueStoreRepository = analogueStoreRepository

    async def on_ready(self):
        print(f'{self.user} is ready!')
