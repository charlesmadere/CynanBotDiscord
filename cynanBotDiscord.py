import asyncio
import sched
import time

import discord
import nest_asyncio

import CynanBotCommon.utils as utils
from analogueSettingsHelper import AnalogueSettingsHelper, AnalogueUserToNotify
from CynanBotCommon.analogueStoreRepository import (AnalogueStoreEntry,
                                                    AnalogueStoreRepository,
                                                    AnalogueStoreStock)


# fixes dumb python async stuff
nest_asyncio.apply()

class CynanBotDiscord(discord.Client):

    def __init__(
        self,
        analogueSettingsHelper: AnalogueSettingsHelper,
        analogueStoreRepository: AnalogueStoreRepository,
        scheduler: sched
    ):
        super().__init__()

        if analogueSettingsHelper is None:
            raise ValueError(f'analogueSettingsHelper argument is malformed: \"{analogueSettingsHelper}\"')
        elif analogueStoreRepository is None:
            raise ValueError(f'analogueStoreRepository argument is malformed: \"{analogueStoreRepository}\"')
        elif scheduler is None:
            raise ValueError(f'scheduler argument is malformed: \"{scheduler}\"')

        self.__analogueSettingsHelper = analogueSettingsHelper
        self.__analogueStoreRepository = analogueStoreRepository
        self.__scheduler = scheduler

    async def on_ready(self):
        print(f'{self.user} is ready!')
        await self.__refreshAnalogueStoreAndScheduleMoreAsync()
        self.__scheduler.run()

    def __refreshAnalogueStoreAndCreatePriorityAvailableMessageText(self, guildMembers):
        storeEntries = self.__analogueStoreRepository.fetchStoreStock().getProducts()
        if not utils.hasItems(storeEntries):
            return None

        priorityStockProductTypes = self.__analogueSettingsHelper.getPriorityStockProductTypes()
        if not utils.hasItems(priorityStockProductTypes):
            return None

        priorityEntriesInStock = list()
        priorityProductTypesInStock = list()
        for storeEntry in storeEntries:
            if storeEntry.inStock() and storeEntry.getProductType() in priorityStockProductTypes:
                priorityEntriesInStock.append(storeEntry)
                priorityProductTypesInStock.append(storeEntry.getProductType())

        if not utils.hasItems(priorityEntriesInStock) or not utils.hasItems(priorityProductTypesInStock):
            return None

        text = '**Priority items are in stock!**'

        for storeEntry in priorityEntriesInStock:
            text = f'{text}\n - {storeEntry.getName()}'

        text = f'{text}\n<{self.__analogueStoreRepository.getStoreUrl()}>\n'

        usersToNotify = self.__analogueSettingsHelper.getUsersToNotify()
        if utils.hasItems(usersToNotify) and guildMembers is not None:
            for user in usersToNotify:
                guildMember = discord.utils.get(guildMembers, id=user.getId())

                print(f'user:{user},guildMember:{guildMember}')

                if guildMember is not None:
                    text = f'{text}\n@{guildMember.mention}'

        return text

    async def __refreshAnalogueStoreAndScheduleMoreAsync(self):
        channelId = self.__analogueSettingsHelper.getChannelId()
        channel = self.get_channel(channelId)

        if channel is None:
            raise RuntimeError(f'Unable to find channel with ID: \"{channelId}\"')

        guild = channel.guild

        if guild is None:
            raise RuntimeError(f'No guild returned for channel \"{channel.name}\" with ID: \"{channelId}\"')

        text = self.__refreshAnalogueStoreAndCreatePriorityAvailableMessageText(guild.members)
        delaySeconds = self.__analogueSettingsHelper.getRefreshEverySeconds()

        if utils.isValidStr(text):
            print(f'======\nSending Analogue stock message to channel \"{channel.name}\":\n{text}\n======')
            await channel.send(text)

            # delay one day before next Analogue store refresh
            delaySeconds = 60 * 60 * 24

        self.__scheduler.enter(
            delay=delaySeconds,
            priority=1,
            action=self.__refreshAnalogueStoreAndScheduleMoreSync
        )

    def __refreshAnalogueStoreAndScheduleMoreSync(self):
        loop = asyncio.get_running_loop()
        loop.run_until_complete(self.__refreshAnalogueStoreAndScheduleMoreAsync())
