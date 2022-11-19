import asyncio
import urllib
from datetime import datetime, timedelta, timezone
from typing import List

import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

import CynanBotCommon.utils as utils
from authRepository import AuthRepository
from CynanBotCommon.timber.timber import Timber
from generalSettingsRepository import GeneralSettingsRepository
from twitchAnnounceChannelsRepository import TwitchAnnounceChannelsRepository
from twitchAnnounceSettingsRepository import TwitchAnnounceSettingsRepository
from twitchLiveUsersRepository import TwitchLiveUsersRepository
from user import User


class CynanBotDiscord(commands.Bot):

    def __init__(
        self,
        authRepository: AuthRepository,
        generalSettingsRepository: GeneralSettingsRepository,
        timber: Timber,
        twitchAnnounceChannelsRepository: TwitchAnnounceChannelsRepository,
        twitchAnnounceSettingsRepository: TwitchAnnounceSettingsRepository,
        twitchLiveUsersRepository: TwitchLiveUsersRepository
    ):
        super().__init__(
            command_prefix = '!',
            intents = discord.Intents.default(),
            status = discord.Status.online
        )

        if authRepository is None:
            raise ValueError(f'authRepository argument is malformed: \"{authRepository}\"')
        elif generalSettingsRepository is None:
            raise ValueError(f'generalSettingsRepository argument is malformed: \"{generalSettingsRepository}\"')
        elif timber is None:
            raise ValueError(f'timber argument is malformed: \"{timber}\"')
        elif twitchAnnounceChannelsRepository is None:
            raise ValueError(f'twitchAnnounceChannelsRepository argument is malformed: \"{twitchAnnounceChannelsRepository}\"')
        elif twitchAnnounceSettingsRepository is None:
            raise ValueError(f'twitchAnnounceSettingsRepository argument is malformed: \"{twitchAnnounceSettingsRepository}\"')
        elif twitchLiveUsersRepository is None:
            raise ValueError(f'twitchLiveUsersRepository argument is malformed: \"{twitchLiveUsersRepository}\"')

        self.__authRepository: AuthRepository = authRepository
        self.__generalSettingsRepository: GeneralSettingsRepository = generalSettingsRepository
        self.__timber: Timber = timber
        self.__twitchAnnounceChannelsRepository: TwitchAnnounceChannelsRepository = twitchAnnounceChannelsRepository
        self.__twitchAnnounceSettingsRepository: TwitchAnnounceSettingsRepository = twitchAnnounceSettingsRepository
        self.__twitchLiveUsersRepository: TwitchLiveUsersRepository = twitchLiveUsersRepository

        now = datetime.now(timezone.utc)
        self.__lastTwitchCheckTime = now - timedelta(minutes = self.__twitchAnnounceSettingsRepository.getAll().getRefreshEveryMinutes())

    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        else:
            raise error

    async def on_ready(self):
        self.__timber.log('CynanBotDiscord', f'{self.user} is ready!')
        self.loop.create_task(self.__beginLooping())

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

        await self.__twitchAnnounceChannelsRepository.addUser(user, ctx.channel.id)

        self.__timber.log('CynanBotDiscord', f'Added `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()}) to Twitch announce users')
        await ctx.send(f'added `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()}) to Twitch announce users')

    async def __beginLooping(self):
        await self.wait_until_ready()

        while not self.is_closed():
            await self.__checkTwitchStreams()

            generalSettings = await self.__generalSettingsRepository.getAllAsync()
            await asyncio.sleep(generalSettings.getRefreshEverySeconds())

    async def __checkTwitchStreams(self):
        now = datetime.now(timezone.utc)
        twitchAnnounceSettings = await self.__twitchAnnounceSettingsRepository.getAllAsync()
        if self.__lastTwitchCheckTime + timedelta(minutes = twitchAnnounceSettings.getRefreshEveryMinutes()) >= now:
            return

        self.__lastTwitchCheckTime = now
        self.__timber.log('CynanBotDiscord', 'Checking for live Twitch streams...')

        twitchLiveUserData = await self.__twitchLiveUsersRepository.fetchTwitchLiveUserData()
        if not utils.hasItems(twitchLiveUserData):
            return

        for twitchLiveUserData in twitchLiveUserData:
            twitchLiveData = twitchLiveUserData.getTwitchLiveData()

            firstLineText = ''
            if twitchLiveData.hasGameName():
                firstLineText = f'{twitchLiveData.getUserLogin()} is now live with {twitchLiveData.getGameName()}!'
            else:
                firstLineText = f'{twitchLiveData.getUserLogin()} is now live!'

            secondLineText = f' https://twitch.tv/{twitchLiveData.getUserLogin()}'

            thirdLineText = ''
            if twitchLiveData.hasTitle():
                thirdLineText = f'\n> {twitchLiveData.getTitle()}'

            discordAnnounceText = f'{firstLineText}{secondLineText}{thirdLineText}'

            user = twitchLiveUserData.getUser()
            announceChannelNames: List[str] = list()

            for discordChannelId in twitchLiveUserData.getDiscordChannelIds():
                channel = await self.__fetchChannel(discordChannelId)
                guildMember = await channel.guild.fetch_member(user.getDiscordId())

                if guildMember is None:
                    self.__timber.log('CynanBotDiscord', f'Couldn\'t find user ID {user.getDiscordId()} in guild {channel.guild.name}, removing them from this channel\'s Twitch announce users...')
                    self.__twitchAnnounceChannelsRepository.removeUser(user, discordChannelId)
                else:
                    announceChannelNames.append(f'{channel.guild.name}:{channel.name}')
                    await channel.send(discordAnnounceText)

            if utils.hasItems(announceChannelNames):
                channelNames = ', '.join(announceChannelNames)
                self.__timber.log('CynanBotDiscord', f'Announced Twitch live stream for {user.getDiscordNameAndDiscriminator()} in {channelNames}')

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

    async def listTwitchUsers(self, ctx):
        if ctx is None:
            raise ValueError(f'ctx argument is malformed: \"{ctx}\"')

        await self.wait_until_ready()

        if not self.__isAuthorAdministrator(ctx):
            return

        twitchAnnounceChannel = await self.__twitchAnnounceChannelsRepository.fetchTwitchAnnounceChannel(ctx.channel.id)
        if twitchAnnounceChannel is None or not twitchAnnounceChannel.hasUsers():
            await ctx.send('no users are currently having their Twitch streams announced in this channel')
            return

        userNames: List[str] = list()
        for user in twitchAnnounceChannel.getUsers():
            # Every user retrieved here _should_ have a Twitch name, as we require it when
            # entering them into the database as a Twitch announce user. But let's just be safe...

            if user.hasTwitchName():
                userNames.append(f' - `{user.getDiscordNameAndDiscriminator()}` (ttv/{user.getTwitchName()})')
            else:
                userNames.append(f' - `{user.getDiscordNameAndDiscriminator()}`')

        userNamesString = '\n'.join(userNames)
        await ctx.send(f'users who are having their Twitch streams announced in this channel:\n{userNamesString}')

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

        userNames: List[str] = list()
        for mention in mentions:
            user = User(
                discordDiscriminator = mention.discriminator,
                discordId = str(mention.id),
                discordName = mention.name
            )

            await self.__twitchAnnounceChannelsRepository.removeUser(user, ctx.channel.id)
            userNames.append(f'`{user.getDiscordNameAndDiscriminator()}`')

        usersString = ', '.join(userNames)
        self.__timber.log('CynanBotDiscord', f'Removed {usersString} from Twitch announce users')
        await ctx.send(f'removed {usersString} from Twitch announce users')
