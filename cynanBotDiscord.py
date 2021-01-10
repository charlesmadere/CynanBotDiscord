import asyncio
import sched
import time

import discord
import nest_asyncio
from discord.ext import commands

import CynanBotCommon.utils as utils
from analogueSettingsHelper import AnalogueSettingsHelper, AnalogueUserToNotify
from CynanBotCommon.analogueStoreRepository import (AnalogueStoreEntry,
                                                    AnalogueStoreRepository,
                                                    AnalogueStoreStock)


class CynanBotDiscord(commands.Bot):

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

    async def addUser(self, ctx):
        await self.wait_until_ready()

        mentions = self.__getMentionsFromCtx(ctx)
        discriminator = int(mentions[0].discriminator)
        _id = int(mentions[0].id)
        name = mentions[0].name

        user = self.__analogueSettingsHelper.addUserToUsersToNotify(
            discriminator=discriminator,
            _id=_id,
            name=name
        )

        if user is not None:
            print(f'Added {user.toStr()} to users to notify ({utils.getNowTimeText()})')
            await ctx.send(f'added `{user.getNameAndDiscriminator()}` to users to notify')

    async def __fetchAllMembers(self):
        await self.wait_until_ready()

        guild = self.__fetchGuild()

        members = await guild.fetch_members(limit=None)
        if members is None:
            raise ValueError(f'Guild \"{guild.name}\" failed to fetch members')

        membersList = members.flatten()
        if not utils.hasItems(membersList):
            raise ValueError(f'Guild \"{guild.name}\" has no members')

        return membersList

    async def __fetchChannel(self):
        await self.wait_until_ready()

        channelId = self.__analogueSettingsHelper.getChannelId()
        channel = await self.fetch_channel(channelId)

        if channel is None:
            raise RuntimeError(f'No channel returned for ID: \"{channelId}\"')

        return channel

    async def __fetchGuild(self):
        await self.wait_until_ready()

        channel = self.__fetchChannel()
        guild = channel.guild

        if guild is None:
            raise RuntimeError(f'No guild returned for channel: \"{channel.name}\"')

        return guild

    async def listPriorityProducts(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        priorityStockProductTypes = self.__analogueSettingsHelper.getPriorityStockProductStrings()

        if utils.hasItems(priorityStockProductTypes):
            productTypesStrings = list()

            for productTypeString in priorityStockProductTypes:
                productTypesStrings.append(f'`{productTypeString}`')

            productTypesString = ', '.join(productTypesStrings)
            await ctx.send(f'Analogue products currently being monitored for availability: {productTypesString}')
        else:
            await ctx.send('no Analogue products are currently being monitored for availability')

    async def listUsers(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        users = self.__analogueSettingsHelper.getUsersToNotify()

        if utils.hasItems(users):
            userNames = list()

            for user in users:
                userNames.append(f'`{user.getNameAndDiscriminator()}`')

            userNamesString = ', '.join(userNames)

            await ctx.send(f'users who will be notified when priority Analogue products are available: {userNamesString}')
        else:
            await ctx.send('no users are set to be notified when priority Analogue products are available')

    def __getMentionsFromCtx(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        message = ctx.message

        if message is None:
            raise ValueError(f'ctx ({ctx}) message is malformed: \"{message}\"')

        mentions = message.mentions

        if not utils.hasItems(mentions):
            raise ValueError(f'No users mentioned: ctx ({ctx}) message: \"{message}\"')

        return mentions

    async def __refreshAnalogueStoreAndCreatePriorityAvailableMessageText(self):
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
            guild = self.__fetchGuild()

            for user in usersToNotify:
                guildMember = await guild.fetch_member(user.getId())

                if guildMember is None:
                    print(f'Unable to find user {user.toStr()} in guild {guild.name}')
                else:
                    text = f'{text}\n - {guildMember.mention}'

        return text

    async def __refreshAnalogueStore(self):
        text = await self.__refreshAnalogueStoreAndCreatePriorityAvailableMessageText()
        delaySeconds = self.__analogueSettingsHelper.getRefreshEverySeconds()

        if utils.isValidStr(text):
            channel = self.__fetchChannel()

            print(f'Sending Analogue stock message to channel \"{channel.name}\" ({utils.getNowTimeText}):\n{text}')
            await channel.send(text)

            # delay one day before next Analogue store refresh
            delaySeconds = 60 * 60 * 24

        return delaySeconds

    async def __refreshAnalogueStoreAndWait(self):
        await self.wait_until_ready()

        while not self.is_closed():
            delaySeconds = await self.__refreshAnalogueStore()
            await asyncio.sleep(delaySeconds)

    async def removeUser(self, ctx):
        await self.wait_until_ready()

        mentions = self.__getMentionsFromCtx(ctx)
        _id = int(mentions[0].id)

        user = self.__analogueSettingsHelper.removeUserFromUsersToNotify(
            _id=_id
        )

        if user is not None:
            print(f'Removed {user.toStr()} from users to notify ({utils.getNowTimeText()})')
            await ctx.send(f'removed `{user.getNameAndDiscriminator()}` from users to notify')
