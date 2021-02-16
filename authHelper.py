import json
import os

import CynanBotCommon.utils as utils


class AuthHelper():

    def __init__(
        self,
        authFile: str = 'authFile.json'
    ):
        if not utils.isValidStr(authFile):
            raise ValueError(f'argument is malformed: \"{authFile}\"')

        self.__authFile = authFile

        if not os.path.exists(authFile):
            raise FileNotFoundError(f'Auth file not found: \"{authFile}\"')

        with open(authFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from auth file: \"{authFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of auth file \"{authFile}\" is empty')

        token = jsonContents.get('token')
        if not utils.isValidStr(token):
            raise ValueError(f'Auth file \"{authFile}\" has malformed token: \"{token}\"')
        self.__token = token

    def getToken(self) -> str:
        return self.__token
