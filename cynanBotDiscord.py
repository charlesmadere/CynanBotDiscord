import asyncio
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

import CynanBotCommon.utils as utils
from analogueSettingsHelper import AnalogueSettingsHelper
from authHelper import AuthHelper
from CynanBotCommon.analogueStoreRepository import (AnalogueStoreRepository,
                                                    AnalogueStoreStock)
from twitchAccounceSettingsHelper import TwitchAnnounceSettingsHelper


class CynanBotDiscord(commands.Bot):

    def __init__(
        self,
        analogueSettingsHelper: AnalogueSettingsHelper,
        analogueStoreRepository: AnalogueStoreRepository,
        authHelper: AuthHelper,
        twitchAnnounceSettingsHelper: TwitchAnnounceSettingsHelper
    ):
        super().__init__(
            command_prefix = '!',
            intents = discord.Intents.default(),
            status = discord.Status.online
        )

        if analogueSettingsHelper is None:
            raise ValueError(f'analogueSettingsHelper argument is malformed: \"{analogueSettingsHelper}\"')
        elif analogueStoreRepository is None:
            raise ValueError(f'analogueStoreRepository argument is malformed: \"{analogueStoreRepository}\"')
        elif authHelper is None:
            raise ValueError(f'authHelper argument is malformed: \"{authHelper}\"')
        elif twitchAnnounceSettingsHelper is None:
            raise ValueError(f'twitchAnnounceSttingsHelper argument is malformed: \"{twitchAnnounceSettingsHelper}\"')

        self.__analogueSettingsHelper = analogueSettingsHelper
        self.__analogueStoreRepository = analogueStoreRepository
        self.__authHelper = authHelper
        self.__twitchAnnounceSettingsHelper = twitchAnnounceSettingsHelper

        self.__analogueMessageCoolDown = timedelta(minutes = 5)
        self.__lastAnalogueMessageTime = datetime.now() - self.__analogueMessageCoolDown

    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        else:
            raise error

    async def on_ready(self):
        print(f'{self.user} is ready!')
        self.loop.create_task(self.__refreshAnalogueStoreAndWait())

    async def addUser(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        mentions = self.__getMentionsFromCtx(ctx)
        users = list()

        for mention in mentions:
            discriminator = int(mention.discriminator)
            _id = int(mention.id)
            name = mention.name

            user = self.__analogueSettingsHelper.addUserToUsersToNotify(
                discriminator=discriminator,
                _id=_id,
                name=name
            )

            users.append(f'`{user.getNameAndDiscriminator()}`')

        usersString = ', '.join(users)
        print(f'Added {usersString} to users to notify ({utils.getNowTimeText()})')
        await ctx.send(f'added {usersString} to users to notify')

    async def analogue(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        now = datetime.now()
        if now - self.__analogueMessageCoolDown <= self.__lastAnalogueMessageTime:
            return

        self.__lastAnalogueMessageTime = now

        try:
            result = self.__analogueStoreRepository.fetchStoreStock()
            await ctx.send(result.toStr(includePrices = True))
        except (RuntimeError, ValueError) as e:
            print(f'Error fetching Analogue stock: {e}')
            await ctx.send('⚠ Error fetching Analogue stock')

    async def __createPriorityStockAvailableMessageText(self, storeStock: AnalogueStoreStock):
        if storeStock is None:
            raise ValueError(f'storeStock argument is malformed: \"{storeStock}\"')

        storeEntries = storeStock.getProducts()
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

    def __isAuthorAdministrator(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        roles = ctx.author.roles

        if utils.hasItems(roles):
            for role in roles:
                if role.permissions.administrator:
                    return True

        return False

    async def listPriorityProducts(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

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

        if not self.__isAuthorAdministrator(ctx):
            return

        users = self.__analogueSettingsHelper.getUsersToNotify()

        if utils.hasItems(users):
            userNames = list()

            for user in users:
                userNames.append(f'`{user.getNameAndDiscriminator()}`')

            userNamesString = ', '.join(userNames)
            await ctx.send(f'users who will be notified when priority Analogue products are available: {userNamesString}')
        else:
            await ctx.send('no users are set to be notified when priority Analogue products are available')

    async def __refreshAnalogueStore(self):
        storeStock = self.__analogueStoreRepository.fetchStoreStock()

        text = None
        if storeStock is not None:
            text = await self.__createPriorityStockAvailableMessageText(storeStock)

        delaySeconds = self.__analogueSettingsHelper.getRefreshEverySeconds()

        if utils.isValidStr(text):
            channel = self.__fetchChannel()

            print(f'Sending Analogue stock message to channel \"{channel.name}\" ({utils.getNowTimeText(includeSeconds = True)}):\n{text}')
            await channel.send(text)

            delaySeconds = self.__analogueSettingsHelper.getRefreshDelayAfterPriorityStockFoundSeconds()
        elif storeStock is None:
            # An error must have occurred when fetching Analogue's store stock, so let's delay a
            # little bit longer before the next refresh attempt.
            delaySeconds = 2 * delaySeconds

        return delaySeconds

    async def __refreshAnalogueStoreAndWait(self):
        await self.wait_until_ready()

        while not self.is_closed():
            delaySeconds = await self.__refreshAnalogueStore()
            await asyncio.sleep(delaySeconds)

    async def removeUser(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        mentions = self.__getMentionsFromCtx(ctx)
        users = list()

        for mention in mentions:
            _id = int(mention.id)
            user = self.__analogueSettingsHelper.removeUserFromUsersToNotify(_id)

            if user is not None:
                users.append(f'`{user.getNameAndDiscriminator()}`')

        usersString = ', '.join(users)
        print(f'Removed {usersString} from users to notify ({utils.getNowTimeText()})')
        await ctx.send(f'removed {usersString} from users to notify')
