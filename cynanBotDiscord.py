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
from CynanBotCommon.timedDict import TimedDict
from generalSettingsHelper import GeneralSettingsHelper
from twitchAccounceSettingsHelper import TwitchAnnounceSettingsHelper
from twitchLiveHelper import TwitchLiveHelper


class CynanBotDiscord(commands.Bot):

    def __init__(
        self,
        analogueSettingsHelper: AnalogueSettingsHelper,
        analogueStoreRepository: AnalogueStoreRepository,
        authHelper: AuthHelper,
        generalSettingsHelper: GeneralSettingsHelper,
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
        elif twitchAnnounceSettingsHelper is None:
            raise ValueError(f'twitchAnnounceSttingsHelper argument is malformed: \"{twitchAnnounceSettingsHelper}\"')
        elif twitchLiveHelper is None:
            raise ValueError(f'twitchLiveHelper argument is malformed: \"{twitchLiveHelper}\"')

        self.__analogueSettingsHelper = analogueSettingsHelper
        self.__analogueStoreRepository = analogueStoreRepository
        self.__authHelper = authHelper
        self.__generalSettingsHelper = generalSettingsHelper
        self.__twitchAnnounceSettingsHelper = twitchAnnounceSettingsHelper
        self.__twitchLiveHelper = twitchLiveHelper

        now = datetime.now()
        self.__analogueCommandCoolDown = timedelta(minutes = 10)
        self.__lastAnalogueCommandMessageTime = now - self.__analogueCommandCoolDown
        self.__lastAnalogueCheckTime = now - timedelta(seconds = self.__analogueSettingsHelper.getRefreshEverySeconds())
        self.__lastTwitchCheckTime = now - timedelta(seconds = self.__twitchAnnounceSettingsHelper.getRefreshEverySeconds())
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

        users = list()

        for mention in mentions:
            discriminator = int(mention.discriminator)
            _id = int(mention.id)
            name = mention.name

            user = self.__analogueSettingsHelper.addUserToUsersToNotify(
                discriminator = discriminator,
                _id = _id,
                name = name
            )

            users.append(f'`{user.getNameAndDiscriminator()}`')

        usersString = ', '.join(users)
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

        mention = mentions[0]

        user = self.__twitchAnnounceSettingsHelper.addUserToTwitchAnnounceUsers(
            discordDiscriminator = int(mention.discriminator),
            discordId = int(mention.id),
            discordName = mention.name,
            twitchName = content[len(content) - 1]
        )

        print(f'Added `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()}) to twitch announce users ({utils.getNowTimeText()})')
        await ctx.send(f'added `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()}) to twitch announce users')

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

        storeStock = self.__analogueStoreRepository.fetchStoreStock()

        text = None
        if storeStock is not None:
            text = await self.__createPriorityStockAvailableMessageText(storeStock)

        if utils.isValidStr(text):
            print(f'Sending Analogue stock message ({utils.getNowTimeText(includeSeconds = True)}):\n{text}')

            for channelId in channelIds:
                channel = self.__fetchChannel(channelId)
                await channel.send(text)

    async def __checkTwitchStreams(self):
        now = datetime.now()

        if self.__lastTwitchCheckTime + timedelta(seconds = self.__twitchAnnounceSettingsHelper.getRefreshEverySeconds()) >= now:
            return

        self.__lastTwitchCheckTime = now

        twitchAnnounceUsers = self.__twitchAnnounceSettingsHelper.getAllTwitchAnnounceUsers()
        if not utils.hasItems(twitchAnnounceUsers):
            return

        liveTwitchUsers = self.__twitchLiveHelper.whoIsLive(twitchAnnounceUsers)
        if not utils.hasItems(liveTwitchUsers):
            return

        removeTheseUsers = list()

        for liveTwitchUser in liveTwitchUsers:
            lastAnnounceTime = self.__liveTwitchUsersAnnounceTimes.get(liveTwitchUser.getTwitchName().lower())

            if lastAnnounceTime is not None and lastAnnounceTime >= now:
                removeTheseUsers.append(liveTwitchUser)
            else:
                self.__liveTwitchUsersAnnounceTimes[liveTwitchUser.getTwitchName().lower()] = now

        if utils.hasItems(removeTheseUsers):
            for removeThisUser in removeTheseUsers:
                liveTwitchUsers.remove(removeThisUser)

        if not utils.hasItems(liveTwitchUsers):
            return

        for liveTwitchUser in liveTwitchUsers:
            twitchAnnounceServers = self.__twitchAnnounceSettingsHelper.getTwitchAnnounceServersForUser(
                discordUserId = liveTwitchUser.getDiscordId()
            )

            if not utils.hasItems(twitchAnnounceServers):
                continue

            for twitchAnnounceServer in twitchAnnounceServers:
                channel = self.__fetchChannel(twitchAnnounceServer.getDiscordChannelId())
                guildMember = await channel.guild.fetch_member(liveTwitchUser.getDiscordId())

                if guildMember is not None:
                    await channel.send(f'{liveTwitchUser.getDiscordName()} is now live! https://twitch.tv/{liveTwitchUser.getTwitchName()}')

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

        if utils.hasItems(users):
            userNames = list()

            for user in users:
                userNames.append(f'`{user.getNameAndDiscriminator()}`')

            userNamesString = ', '.join(userNames)
            await ctx.send(f'users who will be notified when priority Analogue products are available: {userNamesString}')
        else:
            await ctx.send('no users are set to be notified when priority Analogue products are available')

    async def listTwitchUsers(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        # TODO

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

        users = list()

        for mention in mentions:
            user = self.__analogueSettingsHelper.removeUserFromUsersToNotify(int(mention.id))

            if user is not None:
                users.append(f'`{user.getNameAndDiscriminator()}`')

        usersString = ', '.join(users)
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

        users = list()

        for mention in mentions:
            user = self.__twitchAnnounceSettingsHelper.removeUserFromTwitchAnnounceUsers(
                discordId = int(mention.id)
            )

            users.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        usersString = ', '.join(users)
        print(f'Removed {usersString} from twitch announce users ({utils.getNowTimeText()})')
        await ctx.send(f'removed {usersString} from twitch announce users')
