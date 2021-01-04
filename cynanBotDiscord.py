import asyncio
import sched
import time

import discord
import nest_asyncio
from discord.ext.commands import Bot

import CynanBotCommon.utils as utils
from analogueSettingsHelper import AnalogueSettingsHelper, AnalogueUserToNotify
from CynanBotCommon.analogueStoreRepository import (AnalogueStoreEntry,
                                                    AnalogueStoreRepository,
                                                    AnalogueStoreStock)


class CynanBotDiscord(Bot):

    def __init__(
        self,
        analogueSettingsHelper: AnalogueSettingsHelper,
        analogueStoreRepository: AnalogueStoreRepository
    ):
        super().__init__(
            command_prefix='!',
            intents=discord.Intents.default(),
            status=discord.Status.online
        )

        if analogueSettingsHelper is None:
            raise ValueError(f'analogueSettingsHelper argument is malformed: \"{analogueSettingsHelper}\"')
        elif analogueStoreRepository is None:
            raise ValueError(f'analogueStoreRepository argument is malformed: \"{analogueStoreRepository}\"')

        self.__analogueSettingsHelper = analogueSettingsHelper
        self.__analogueStoreRepository = analogueStoreRepository

    async def on_ready(self):
        print(f'{self.user} is ready!')
        self.loop.create_task(self.__refreshAnalogueStoreAndWait())

    async def __refreshAnalogueStoreAndCreatePriorityAvailableMessageText(self, guild):
        if guild is None:
            raise ValueError(f'guild argument is malformed: \"{guild}\"')

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
        if utils.hasItems(usersToNotify):
            for user in usersToNotify:
                guildMember = await guild.fetch_member(user.getId())

                if guildMember is None:
                    print(f'Unable to find user {user.toStr()} in guild {guild.name}')
                else:
                    text = f'{text}\n - {guildMember.mention}'

        return text

    async def __refreshAnalogueStore(self, channel, guild):
        if channel is None:
            raise ValueError(f'channel argument is malformed: \"{channel}\"')
        elif guild is None:
            raise ValueError(f'guild argument is malformed: \"{guild}\"')

        text = await self.__refreshAnalogueStoreAndCreatePriorityAvailableMessageText(guild)
        delaySeconds = self.__analogueSettingsHelper.getRefreshEverySeconds()

        if utils.isValidStr(text):
            print(f'Sending Analogue stock message to channel \"{channel.name}\" ({utils.getNowTimeText}):\n{text}')
            await channel.send(text)

            # delay one day before next Analogue store refresh
            delaySeconds = 60 * 60 * 24

        return delaySeconds

    async def __refreshAnalogueStoreAndWait(self):
        await self.wait_until_ready()

        channelId = self.__analogueSettingsHelper.getChannelId()
        channel = await self.fetch_channel(channelId)

        if channel is None:
            raise RuntimeError(f'Unable to find channel with ID: \"{channelId}\"')

        guild = channel.guild

        if guild is None:
            raise RuntimeError(f'No guild returned for channel \"{channel.name}\" with ID: \"{channelId}\"')

        while not self.is_closed():
            delaySeconds = await self.__refreshAnalogueStore(channel, guild)
            await asyncio.sleep(delaySeconds)
