import json
import os

import requests
from requests import ConnectionError, HTTPError, Timeout
from urllib3.exceptions import MaxRetryError, NewConnectionError

import CynanBotCommon.utils as utils


class TwitchTokensRepository():

    def __init__(
        self,
        twitchTokensFile: str = 'twitchTokensRepository.json'
    ):
        if not utils.isValidStr(twitchTokensFile):
            raise ValueError(f'twitchTokensFile argument is malformed: \"{twitchTokensFile}\"')

        self.__twitchTokensFile = twitchTokensFile

    def getAccessToken(self) -> str:
        jsonContents = self.__readJson()
        accessToken = jsonContents['accessToken']

        if not utils.isValidStr(accessToken):
            raise ValueError(f'accessToken is malformed: \"{accessToken}\"')

        return accessToken

    def getRefreshToken(self) -> str:
        jsonContents = self.__readJson()
        refreshToken = jsonContents['refreshToken']

        if not utils.isValidStr(refreshToken):
            raise ValueError(f'refreshToken is malformed: \"{refreshToken}\"')

        return refreshToken

    def __readJson(self) -> dict:
        if not os.path.exists(self.__twitchTokensFile):
            raise FileNotFoundError(f'Twitch tokens file not found: \"{self.__twitchTokensFile}\"')

        with open(self.__twitchTokensFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Twitch tokens file: \"{self.__twitchTokensFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Twitch tokens file \"{self.__twitchTokensFile}\" is empty')

        return jsonContents

    def refreshTokens(
        self,
        clientId: str,
        clientSecret: str
    ):
        if not utils.isValidStr(clientId):
            raise ValueError(f'clientId argument is malformed: \"{clientId}\"')
        elif not utils.isValidStr(clientSecret):
            raise ValueError(f'clientSecret argument is malformed: \"{clientSecret}\"')

        print(f'Requesting new Twitch tokens... ({utils.getNowTimeText(includeSeconds = True)})')

        rawResponse = None
        try:
            rawResponse = requests.post(
                url = self.oauth2TokenUrl,
                params = {
                    'client_id': clientId,
                    'client_secret': clientSecret,
                    'grant_type': 'refresh_token',
                    'refresh_token': self.getRefreshToken()
                }
            )
        except (ConnectionError, HTTPError, MaxRetryError, NewConnectionError, Timeout) as e:
            print(f'Exception occurred when attempting to request new Twitch tokens: {e}')
            raise RuntimeError(f'Exception occurred when attempting to request new Twitch tokens: {e}')

        jsonResponse = rawResponse.json()

        if 'access_token' not in jsonResponse or len(jsonResponse['access_token']) == 0:
            raise ValueError(f'Received malformed \"access_token\" Twitch token: {jsonResponse}')
        elif 'refresh_token' not in jsonResponse or len(jsonResponse['refresh_token']) == 0:
            raise ValueError(f'Received malformed \"refresh_token\" Twitch token: {jsonResponse}')

        jsonContents = {
            'accessToken': jsonResponse['access_token'],
            'refreshToken': jsonResponse['refresh_token']
        }

        with open(self.__twitchTokensFile, 'w') as file:
            json.dump(jsonContents, file, indent = 4, sort_keys = True)

        print(f'Saved new Twitch tokens ({utils.getNowTimeText(includeSeconds = True)})')
