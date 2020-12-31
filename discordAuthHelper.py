import json
import os

import CynanBotCommon.utils as utils


class DiscordAuthHelper():

    def __init__(
        self,
        discordAuthFile: str = 'discordAuthFile.json'
    ):
        self.__discordAuthFile = discordAuthFile

        if not os.path.exists(discordAuthFile):
            raise FileNotFoundError(f'Discord auth file not found: \"{discordAuthFile}\"')

        with open(discordAuthFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from discord auth file: \"{discordAuthFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of discord auth file \"{discordAuthFile}\" is empty')

        token = jsonContents.get('token')
        if not utils.isValidStr(token):
            raise ValueError(f'Discord auth file \"{discordAuthFile}\" has malformed token: \"{token}\"')
        self.__token = token

    def getToken(self):
        return self.__token
