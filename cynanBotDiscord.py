import asyncio
import urllib
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

import CynanBotCommon.utils as utils
from analogueAnnounceChannelsRepository import (
    AnalogueAnnounceChannel, AnalogueAnnounceChannelsRepository)
from analogueSettingsHelper import AnalogueSettingsHelper
from authHelper import AuthHelper
from CynanBotCommon.analogueStoreRepository import (AnalogueProductType,
                                                    AnalogueStoreRepository,
                                                    AnalogueStoreStock)
from generalSettingsHelper import GeneralSettingsHelper
from twitchAnnounceChannelsRepository import TwitchAnnounceChannelsRepository
from twitchAnnounceSettingsHelper import TwitchAnnounceSettingsHelper
from twitchLiveUsersRepository import TwitchLiveUsersRepository
from user import User


class CynanBotDiscord(commands.Bot):

    def __init__(
        self,
        analogueAnnounceChannelsRepository: AnalogueAnnounceChannelsRepository,
        analogueSettingsHelper: AnalogueSettingsHelper,
        analogueStoreRepository: AnalogueStoreRepository,
        authHelper: AuthHelper,
        generalSettingsHelper: GeneralSettingsHelper,
        twitchAnnounceChannelsRepository: TwitchAnnounceChannelsRepository,
        twitchAnnounceSettingsHelper: TwitchAnnounceSettingsHelper,
        twitchLiveUsersRepository: TwitchLiveUsersRepository
    ):
        super().__init__(
            command_prefix = '!',
            intents = discord.Intents.default(),
            status = discord.Status.online
        )

        if analogueAnnounceChannelsRepository is None:
            raise ValueError(f'analogueAnnounceChannelsRepository argument is malformed: \"{analogueAnnounceChannelsRepository}\"')
        elif analogueSettingsHelper is None:
            raise ValueError(f'analogueSettingsHelper argument is malformed: \"{analogueSettingsHelper}\"')
        elif analogueStoreRepository is None:
            raise ValueError(f'analogueStoreRepository argument is malformed: \"{analogueStoreRepository}\"')
        elif authHelper is None:
            raise ValueError(f'authHelper argument is malformed: \"{authHelper}\"')
        elif generalSettingsHelper is None:
            raise ValueError(f'generalSettingsHelper argument is malformed: \"{generalSettingsHelper}\"')
        elif twitchAnnounceChannelsRepository is None:
            raise ValueError(f'twitchAnnounceChannelsRepository argument is malformed: \"{twitchAnnounceChannelsRepository}\"')
        elif twitchAnnounceSettingsHelper is None:
            raise ValueError(f'twitchAnnounceSttingsHelper argument is malformed: \"{twitchAnnounceSettingsHelper}\"')
        elif twitchLiveUsersRepository is None:
            raise ValueError(f'twitchLiveUsersRepository argument is malformed: \"{twitchLiveUsersRepository}\"')

        self.__analogueAnnounceChannelsRepository = analogueAnnounceChannelsRepository
        self.__analogueSettingsHelper = analogueSettingsHelper
        self.__analogueStoreRepository = analogueStoreRepository
        self.__authHelper = authHelper
        self.__generalSettingsHelper = generalSettingsHelper
        self.__twitchAnnounceChannelsRepository = twitchAnnounceChannelsRepository
        self.__twitchAnnounceSettingsHelper = twitchAnnounceSettingsHelper
        self.__twitchLiveUsersRepository = twitchLiveUsersRepository

        now = datetime.utcnow()
        self.__analogueCommandCoolDown = timedelta(minutes = 10)
        self.__lastAnalogueCommandMessageTime = now - self.__analogueCommandCoolDown
        self.__lastAnalogueCheckTime = now - timedelta(seconds = self.__analogueSettingsHelper.getRefreshEverySeconds())
        self.__lastTwitchCheckTime = now - timedelta(minutes = self.__twitchAnnounceSettingsHelper.getRefreshEveryMinutes())

    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        else:
            raise error

    async def on_ready(self):
        print(f'{self.user} is ready!')
        self.loop.create_task(self.__refreshAnalogueStoreAndWait())

    async def addAnaloguePriorityProduct(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        content = utils.getCleanedSplits(ctx.message.content)
        if not utils.hasItems(content) or len(content) < 2:
            await ctx.send('please specify the name of the Analogue product you want to monitor for availability. example:\n`!addAnaloguePriorityProduct Super Nt`')
            return

        productNameString = ' '.join(content[1:])
        analoguePriorityProduct = AnalogueProductType.fromStr(productNameString)

        self.__analogueAnnounceChannelsRepository.addAnaloguePriorityProduct(
            analoguePriorityProduct = analoguePriorityProduct,
            discordChannelId = ctx.channel.id
        )

        print(f'Added Analogue priority product monitor for {analoguePriorityProduct.toStr()} in {ctx.channel.guild.name}:{ctx.channel.name} ({utils.getNowTimeText()})')
        await ctx.send(f'added Analogue priority product monitor for `{analoguePriorityProduct.toStr()}`')

    async def addAnalogueUser(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        mentions = self.__getMentionsFromCtx(ctx)
        if not utils.hasItems(mentions):
            await ctx.send('please mention the user(s) you want to add')
            return

        users = list()
        for mention in mentions:
            user = User(
                discordDiscriminator = mention.discriminator,
                discordId = str(mention.id),
                discordName = mention.name
            )

            self.__analogueAnnounceChannelsRepository.addUser(user, ctx.channel.id)
            users.append(user)

        usersStrings = list()
        for user in users:
            usersStrings.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        usersString = ', '.join(usersStrings)
        print(f'Added Analogue user(s) to notify in {ctx.channel.guild.name}:{ctx.channel.name} ({utils.getNowTimeText()})')
        await ctx.send(f'added {usersString} to Analogue announce users')

    async def addTwitchUser(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        mentions = self.__getMentionsFromCtx(ctx)
        if not utils.hasItems(mentions):
            await ctx.send('please mention the user you want to add')
            return

        content = utils.getCleanedSplits(ctx.message.content)
        if not utils.hasItems(content):
            await ctx.send('please give the user\'s twitch handle, as taken directly from their ttv url')
            return

        if len(content) != 3:
            await ctx.send('example command: `!addTwitchUser @CynanBot cynanbot` (the last parameter is their ttv handle)')
            return

        url = urllib.parse.urlparse(content[len(content) - 1])
        twitchName = None

        if '/' in url.path:
            indexOfSlash = url.path.index('/')
            twitchName = url.path[indexOfSlash + 1:len(url.path)]
        else:
            twitchName = url.path

        if not utils.isValidStr(twitchName):
            await ctx.send('example command: `!addTwitchUser @CynanBot cynanbot` (the last parameter is their ttv handle)')
            return

        user = User(
            discordDiscriminator = mentions[0].discriminator,
            discordId = str(mentions[0].id),
            discordName = mentions[0].name,
            twitchName = twitchName
        )

        self.__twitchAnnounceChannelsRepository.addUser(user, ctx.channel.id)

        print(f'Added `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()}) to Twitch announce users ({utils.getNowTimeText()})')
        await ctx.send(f'added `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()}) to Twitch announce users')

    async def analogue(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        now = datetime.utcnow()
        if self.__lastAnalogueCommandMessageTime + self.__analogueCommandCoolDown >= now:
            return

        self.__lastAnalogueCommandMessageTime = now

        try:
            result = self.__analogueStoreRepository.fetchStoreStock()
            await ctx.send(result.toStr(includePrices = True))
        except (RuntimeError, ValueError) as e:
            print(f'Error fetching Analogue stock: {e}')
            await ctx.send('⚠ Error fetching Analogue stock')

    async def __checkAnalogueStoreStock(self):
        now = datetime.utcnow()

        if self.__lastAnalogueCheckTime + timedelta(seconds = self.__analogueSettingsHelper.getRefreshEverySeconds()) >= now:
            return

        self.__lastAnalogueCheckTime = now

        analogueAnnounceChannels = self.__analogueAnnounceChannelsRepository.fetchAnalogueAnnounceChannels()
        if not utils.hasItems(analogueAnnounceChannels):
            return

        storeStock = None
        try:
            storeStock = self.__analogueStoreRepository.fetchStoreStock()
        except (RuntimeError, ValueError):
            return

        for analogueAnnounceChannel in analogueAnnounceChannels:
            text = await self.__createPriorityStockAvailableMessageText(
                analogueAnnounceChannel = analogueAnnounceChannel,
                storeStock = storeStock
            )

            if utils.isValidStr(text):
                channel = await self.__fetchChannel(analogueAnnounceChannel.getDiscordChannelId())
                await channel.send(text)
                print(f'Announced Analogue store stock in {channel.guild.name}:{channel.name}')

    async def __checkTwitchStreams(self):
        now = datetime.utcnow()

        if self.__lastTwitchCheckTime + timedelta(minutes = self.__twitchAnnounceSettingsHelper.getRefreshEveryMinutes()) >= now:
            return

        self.__lastTwitchCheckTime = now

        twitchLiveUserData = self.__twitchLiveUsersRepository.fetchTwitchLiveUserData()
        if not utils.hasItems(twitchLiveUserData):
            return

        for twitchLiveUserData in twitchLiveUserData:
            twitchLiveData = twitchLiveUserData.getTwitchLiveData()

            firstLineText = ''
            if twitchLiveData.hasGameName():
                firstLineText = f'{twitchLiveData.getUserName()} is now live with {twitchLiveData.getGameName()}!'
            else:
                firstLineText = f'{twitchLiveData.getUserName()} is now live!'

            secondLineText = f' https://twitch.tv/{twitchLiveData.getUserName()}'

            thirdLineText = ''
            if twitchLiveData.hasTitle():
                thirdLineText = f'\n> {twitchLiveData.getTitle()}'

            discordAnnounceText = f'{firstLineText}{secondLineText}{thirdLineText}'

            user = twitchLiveUserData.getUser()
            announceChannelNames = list()

            for discordChannelId in twitchLiveUserData.getDiscordChannelIds():
                channel = await self.__fetchChannel(discordChannelId)
                guildMember = await channel.guild.fetch_member(user.getDiscordId())

                if guildMember is None:
                    print(f'Couldn\'t find user ID {user.getDiscordId()} in guild {channel.guild.name}, removing them from this channel\'s Twitch announce users...')
                    self.__twitchAnnounceChannelsRepository.removeUser(user, discordChannelId)
                else:
                    announceChannelNames.append(f'{channel.guild.name}:{channel.name}')
                    await channel.send(discordAnnounceText)

            if utils.hasItems(announceChannelNames):
                channelNames = ', '.join(announceChannelNames)
                print(f'Announced Twitch live stream for {user.getDiscordNameAndDiscriminator()} in {channelNames}')

    async def __createPriorityStockAvailableMessageText(
        self,
        analogueAnnounceChannel: AnalogueAnnounceChannel,
        storeStock: AnalogueStoreStock
    ):
        if analogueAnnounceChannel is None:
            raise ValueError(f'analogueAnnounceChannel argument is malformed: \"{analogueAnnounceChannel}\"')
        elif storeStock is None:
            raise ValueError(f'storeStock argument is malformed: \"{storeStock}\"')

        if not storeStock.hasProducts():
            return None
        elif not analogueAnnounceChannel.hasAnaloguePriorityProducts():
            return None
        elif not analogueAnnounceChannel.hasUsers():
            return None

        storeEntries = storeStock.getProducts()
        priorityStockProductTypes = analogueAnnounceChannel.getAnaloguePriorityProducts()

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
            text = f'{text}\n - {storeEntry.getName()} {storeEntry.getPrice()}'

        text = f'{text}\n<{self.__analogueStoreRepository.getStoreUrl()}>\n'

        if analogueAnnounceChannel.hasUsers():
            guild = await self.__fetchGuild(analogueAnnounceChannel.getDiscordChannelId())

            for user in analogueAnnounceChannel.getUsers():
                guildMember = await guild.fetch_member(user.getDiscordId())

                if guildMember is not None:
                    text = f'{text}\n - {guildMember.mention}'

        return text

    async def __fetchChannel(self, channelId: int):
        if not utils.isValidNum(channelId):
            raise ValueError(f'channelId argument is malformed: \"{channelId}\"')

        await self.wait_until_ready()
        channel = await self.fetch_channel(channelId)

        if channel is None:
            raise RuntimeError(f'No channel returned for ID: \"{channelId}\"')

        return channel

    async def __fetchGuild(self, channelId: int):
        if not utils.isValidNum(channelId):
            raise ValueError(f'channelId argument is malformed: \"{channelId}\"')

        await self.wait_until_ready()

        channel = await self.__fetchChannel(channelId)
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

        return message.mentions

    def __isAuthorAdministrator(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        roles = ctx.author.roles

        if utils.hasItems(roles):
            for role in roles:
                if role.permissions.administrator:
                    return True

        return False

    async def listAnaloguePriorityProducts(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        analogueAnnounceChannel = self.__analogueAnnounceChannelsRepository.fetchAnalogueAnnounceChannel(ctx.channel.id)
        if analogueAnnounceChannel is None or not analogueAnnounceChannel.hasAnaloguePriorityProducts():
            await ctx.send('no priority Analogue products are being checked for in this channel')
            return

        productNames = list()
        for product in analogueAnnounceChannel.getAnaloguePriorityProducts():
            productNames.append(f'`{product.toStr()}`')

        productNamesString = ', '.join(productNames)
        await ctx.send(f'priority Analogue products in this channel: {productNamesString}')

    async def listAnalogueUsers(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        analogueAnnounceChannel = self.__analogueAnnounceChannelsRepository.fetchAnalogueAnnounceChannel(ctx.channel.id)
        if not analogueAnnounceChannel.hasUsers():
            await ctx.send('no users will be notified of priority Analogue products in this channel')
            return

        userNames = list()
        for user in analogueAnnounceChannel.getUsers():
            userNames.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        userNamesString = ', '.join(userNames)
        await ctx.send(f'users who will be notified when priority Analogue products are available: {userNamesString}')

    async def listTwitchUsers(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        twitchAnnounceChannel = self.__twitchAnnounceChannelsRepository.fetchTwitchAnnounceChannel(ctx.channel.id)
        if twitchAnnounceChannel is None or not twitchAnnounceChannel.hasUsers():
            await ctx.send('no users are currently having their Twitch streams announced in this channel')
            return

        userNames = list()
        for user in twitchAnnounceChannel.getUsers():
            # Every user retrieved here _should_ have a Twitch name, as we require it when
            # entering them into the database as a Twitch announce user. But let's just be safe...

            if user.hasTwitchName():
                userNames.append(f' - `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()})')
            else:
                userNames.append(f' - `{user.getDiscordNameAndDiscriminator()}`')

        userNamesString = '\n'.join(userNames)
        await ctx.send(f'users who are having their Twitch streams announced in this channel:\n{userNamesString}')

    async def __refreshAnalogueStoreAndWait(self):
        await self.wait_until_ready()

        while not self.is_closed():
            await self.__checkAnalogueStoreStock()
            await self.__checkTwitchStreams()
            await asyncio.sleep(self.__generalSettingsHelper.getRefreshEverySeconds())

    async def removeAnaloguePriorityProduct(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        content = utils.getCleanedSplits(ctx.message.content)
        if not utils.hasItems(content) or len(content) < 2:
            await ctx.send('please specify the name of the Analogue product you no longer want to be monitoring for availability. example:\n`!removeAnaloguePriorityProduct Super Nt`')
            return

        productNameString = ' '.join(content[1:])
        analoguePriorityProduct = AnalogueProductType.fromStr(productNameString)

        self.__analogueAnnounceChannelsRepository.removeAnaloguePriorityProduct(
            analoguePriorityProduct = analoguePriorityProduct,
            discordChannelId = ctx.channel.id
        )

    async def removeAnalogueUser(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        mentions = self.__getMentionsFromCtx(ctx)
        if not utils.hasItems(mentions):
            await ctx.send('please mention the user(s) you want to remove')
            return

        for mention in mentions:
            user = User(
                discordDiscriminator = mention.discriminator,
                discordId = str(mention.id),
                discordName = mention.name
            )

            self.__analogueAnnounceChannelsRepository.removeUser(user, ctx.channel.id)

        print(f'Removed Analogue user(s) to notify in {ctx.channel.guild.name}:{ctx.channel.name} ({utils.getNowTimeText()})')

    async def removeTwitchUser(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        mentions = self.__getMentionsFromCtx(ctx)
        if not utils.hasItems(mentions):
            await ctx.send('please mention the user(s) you want to remove')
            return

        userNames = list()
        for mention in mentions:
            user = User(
                discordDiscriminator = mention.discriminator,
                discordId = str(mention.id),
                discordName = mention.name
            )

            self.__twitchAnnounceChannelsRepository.removeUser(user, ctx.channel.id)
            userNames.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        usersString = ', '.join(userNames)
        print(f'Removed {usersString} from twitch announce users ({utils.getNowTimeText()})')
        await ctx.send(f'removed {usersString} from twitch announce users')
