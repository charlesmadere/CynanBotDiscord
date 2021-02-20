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
from generalSettingsHelper import GeneralSettingsHelper
from twitchAnnounceChannelsRepository import (TwitchAnnounceChannel,
                                              TwitchAnnounceChannelsRepository)
from twitchAnnounceSettingsHelper import TwitchAnnounceSettingsHelper
from twitchLiveHelper import TwitchLiveHelper
from user import User


class CynanBotDiscord(commands.Bot):

    def __init__(
        self,
        analogueSettingsHelper: AnalogueSettingsHelper,
        analogueStoreRepository: AnalogueStoreRepository,
        authHelper: AuthHelper,
        generalSettingsHelper: GeneralSettingsHelper,
        twitchAnnounceChannelsRepository: TwitchAnnounceChannelsRepository,
        twitchAnnounceSettingsHelper: TwitchAnnounceSettingsHelper,
        twitchLiveHelper: TwitchLiveHelper
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
        elif generalSettingsHelper is None:
            raise ValueError(f'generalSettingsHelper argument is malformed: \"{generalSettingsHelper}\"')
        elif twitchAnnounceChannelsRepository is None:
            raise ValueError(f'twitchAnnounceChannelsRepository argument is malformed: \"{twitchAnnounceChannelsRepository}\"')
        elif twitchAnnounceSettingsHelper is None:
            raise ValueError(f'twitchAnnounceSttingsHelper argument is malformed: \"{twitchAnnounceSettingsHelper}\"')
        elif twitchLiveHelper is None:
            raise ValueError(f'twitchLiveHelper argument is malformed: \"{twitchLiveHelper}\"')

        self.__analogueSettingsHelper = analogueSettingsHelper
        self.__analogueStoreRepository = analogueStoreRepository
        self.__authHelper = authHelper
        self.__generalSettingsHelper = generalSettingsHelper
        self.__twitchAnnounceChannelsRepository = twitchAnnounceChannelsRepository
        self.__twitchAnnounceSettingsHelper = twitchAnnounceSettingsHelper
        self.__twitchLiveHelper = twitchLiveHelper

        now = datetime.now()
        self.__analogueCommandCoolDown = timedelta(minutes = 10)
        self.__lastAnalogueCommandMessageTime = now - self.__analogueCommandCoolDown
        self.__lastAnalogueCheckTime = now - timedelta(seconds = self.__analogueSettingsHelper.getRefreshEverySeconds())
        self.__lastTwitchCheckTime = now - timedelta(minutes = self.__twitchAnnounceSettingsHelper.getRefreshEveryMinutes())
        self.__liveTwitchUsersAnnounceTimes = dict()

    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        else:
            raise error

    async def on_ready(self):
        print(f'{self.user} is ready!')
        self.loop.create_task(self.__refreshAnalogueStoreAndWait())

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

        userNames = list()
        for mention in mentions:
            user = User(
                discordDiscriminator = int(mention.discriminator),
                discordId = mention.id,
                discordName = mention.name
            )

            self.__analogueSettingsHelper.addUser(user)
            userNames.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        usersString = ', '.join(userNames)
        print(f'Added {usersString} to users to notify ({utils.getNowTimeText()})')
        await ctx.send(f'added {usersString} to users to notify')

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

        user = User(
            discordDiscriminator = int(mentions[0].discriminator),
            discordId = int(mentions[0].id),
            discordName = mentions[0].name,
            twitchName = content[len(content) - 1]
        )

        self.__twitchAnnounceChannelsRepository.addUser(user, ctx.channel.id)

        print(f'Added `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()}) to Twitch announce users ({utils.getNowTimeText()})')
        await ctx.send(f'added `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()}) to Twitch announce users')

    async def analogue(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        now = datetime.now()
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
        now = datetime.now()

        if self.__lastAnalogueCheckTime + timedelta(seconds = self.__analogueSettingsHelper.getRefreshEverySeconds()) >= now:
            return

        self.__lastAnalogueCheckTime = now

        channelIds = self.__analogueSettingsHelper.getChannelIds()
        if not utils.hasItems(channelIds):
            return

        # I guess in the future this feature will support multiple channels or something...
        channelId = channelIds[0]

        storeStock = self.__analogueStoreRepository.fetchStoreStock()

        text = None
        if storeStock is not None:
            text = await self.__createPriorityStockAvailableMessageText(storeStock, channelId)

        if utils.isValidStr(text):
            print(f'Sending Analogue stock message ({utils.getNowTimeText(includeSeconds = True)}):\n{text}')
            channel = self.__fetchChannel(channelId)
            await channel.send(text)

    async def __checkTwitchStreams(self):
        now = datetime.now()

        if self.__lastTwitchCheckTime + timedelta(minutes = self.__twitchAnnounceSettingsHelper.getRefreshEveryMinutes()) >= now:
            return

        self.__lastTwitchCheckTime = now

        twitchAnnounceChannels = self.__twitchAnnounceChannelsRepository.fetchTwitchAnnounceChannels()
        if not utils.hasItems(twitchAnnounceChannels):
            return

        userIdsToChannels = dict()
        userIdsToUsers = dict()

        for twitchAnnounceChannel in twitchAnnounceChannels:
            if utils.hasItems(twitchAnnounceChannel.getUsers()):
                for user in twitchAnnounceChannel.getUsers():
                    if user.getDiscordId() not in userIdsToChannels:
                        userIdsToChannels[user.getDiscordId()] = set()

                        if user.getDiscordId() not in userIdsToUsers:
                            userIdsToUsers[user.getDiscordId()] = user

                    userIdsToChannels[user.getDiscordId()].add(twitchAnnounceChannel.getDiscordChannelId())

        removeTheseUserIds = list()

        for userId in userIdsToUsers:
            lastAnnounceTime = self.__liveTwitchUsersAnnounceTimes.get(userId)

            if lastAnnounceTime is not None and lastAnnounceTime >= now:
                removeTheseUserIds.append(userId)

        if utils.hasItems(removeTheseUserIds):
            for userId in removeTheseUserIds:
                del userIdsToChannels[userId]
                del userIdsToUsers[userId]

        if not utils.hasItems(userIdsToChannels) or not utils.hasItems(userIdsToUsers):
            return

        users = list()
        for user in userIdsToUsers.values():
            users.append(user)

        whoIsLive = self.__twitchLiveHelper.whoIsLive(users)

        for user in whoIsLive:
            self.__liveTwitchUsersAnnounceTimes[user.getDiscordId()] = now + timedelta(minutes = self.__twitchAnnounceSettingsHelper.getAnnounceFalloffMinutes())

        for user in whoIsLive:
            userChannels = userIdsToChannels[user.getDiscordId()]

            for userChannel in userChannels:
                channel = self.__fetchChannel(userChannel.getDiscordChannelId())
                guildMember = await channel.guild.fetch_member(user.getDiscordId())

                if guildMember is not None:
                    await channel.send(f'{user.getDiscordName()} is now live! https://twitch.tv/{user.getTwitchName()}')

    async def __createPriorityStockAvailableMessageText(
        self,
        storeStock: AnalogueStoreStock,
        channelId: int
    ):
        if storeStock is None:
            raise ValueError(f'storeStock argument is malformed: \"{storeStock}\"')
        elif not utils.isValidNum(channelId):
            raise ValueError(f'channelId argument is malformed: \"{channelId}\"')

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
            guild = self.__fetchGuild(channelId)

            for user in usersToNotify:
                guildMember = await guild.fetch_member(user.getId())

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

        channel = self.__fetchChannel(channelId)
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

    async def listAnalogueUsers(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        users = self.__analogueSettingsHelper.getUsersToNotify()
        if not utils.hasItems(users):
            await ctx.send('no users are set to be notified when priority Analogue products are available')
            return

        userNames = list()
        for user in users:
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
            await ctx.send('no users are currently having their Twitch streams announced')
            return

        userNames = list()
        for user in twitchAnnounceChannel.getUsers():
            if user.hasTwitchName():
                userNames.append(f'`{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()})')
            else:
                userNames.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        userNamesString = ', '.join(userNames)
        await ctx.send(f'users who are having their Twitch streams announced: {userNamesString}')

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

    async def __refreshAnalogueStoreAndWait(self):
        await self.wait_until_ready()

        while not self.is_closed():
            await self.__checkAnalogueStoreStock()
            await self.__checkTwitchStreams()
            await asyncio.sleep(self.__generalSettingsHelper.getRefreshEverySeconds())

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

        userNames = list()

        for mention in mentions:
            user = User(
                discordDiscriminator = int(mention.discriminator),
                discordId = mention.id,
                discordName = mention.name
            )

            if self.__analogueSettingsHelper.removeUser(user):
                userNames.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        usersString = ', '.join(userNames)
        print(f'Removed {usersString} from users to notify ({utils.getNowTimeText()})')
        await ctx.send(f'removed {usersString} from users to notify')

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
                discordDiscriminator = int(mention.discriminator),
                discordId = mention.id,
                discordName = mention.name
            )

            self.__twitchAnnounceChannelsRepository.removeUser(user, ctx.channel.id)
            userNames.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        usersString = ', '.join(userNames)
        print(f'Removed {usersString} from twitch announce users ({utils.getNowTimeText()})')
        await ctx.send(f'removed {usersString} from twitch announce users')
