import sched
import time

import discord

import CynanBotCommon.utils as utils
from analogueSettingsHelper import AnalogueSettingsHelper
from CynanBotCommon.analogueStoreRepository import (AnalogueStoreEntry,
                                                    AnalogueStoreRepository,
                                                    AnalogueStoreStock)


class CynanBotDiscord(discord.Client):

    def __init__(
        self,
        analogueSettingsHelper: AnalogueSettingsHelper,
        analogueStoreRepository: AnalogueStoreRepository,
        scheduler: sched
    ):
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
        self.__refreshAnalogueStoreAndScheduleMore()

    def __refreshAnalogueStoreAndCreatePriorityAvailableMessageText(self):
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

        text = '**Priority items in stock**'

        for storeEntry in priorityEntriesInStock:
            text = f'{text}\n{storeEntry.getName()}'

        text = f'{text}\n{self.__analogueStoreRepository.getStoreUrl()}'

        usersToNotify = self.__analogueSettingsHelper.getUsersToNotify()
        if utils.hasItems(usersToNotify):
            for userToNotify in usersToNotify:
                text = f'{text}\n@{userToNotify}'

        return text

    def __refreshAnalogueStoreAndScheduleMore(self):
        messageText = self.__refreshAnalogueStoreAndCreatePriorityAvailableMessageText()
        delaySeconds = self.__analogueSettingsHelper.getRefreshEverySeconds()

        if utils.isValidStr(messageText):
            channelId = self.__analogueSettingsHelper.getChannelId()
            channel = self.get_channel(channelId)
            await channel.send(messageText)

            # delay one day before next Analogue store refresh
            delaySeconds = 60 * 60 * 24

        self.__scheduler.enter(
            delay=delaySeconds,
            priority=1,
            action=self.__refreshAnalogueStoreAndScheduleMore()
        )
