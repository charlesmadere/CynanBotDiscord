import json
import os
from json.decoder import JSONDecodeError
from typing import Dict

import requests
from requests import ConnectionError, HTTPError, Timeout
from urllib3.exceptions import MaxRetryError, NewConnectionError

import CynanBotCommon.utils as utils


class TwitchTokensRepository():

    def __init__(
        self,
        oauth2TokenUrl: str = 'https://id.twitch.tv/oauth2/token',
        oauth2ValidateUrl: str = 'https://id.twitch.tv/oauth2/validate',
        twitchTokensFile: str = 'twitchTokensRepository.json'
    ):
        if not utils.isValidUrl(oauth2TokenUrl):
            raise ValueError(f'oauth2TokenUrl argument is malformed: \"{oauth2TokenUrl}\"')
        elif not utils.isValidUrl(oauth2ValidateUrl):
            raise ValueError(f'oauth2ValidateUrl argument is malformed: \"{oauth2ValidateUrl}\"')
        elif not utils.isValidStr(twitchTokensFile):
            raise ValueError(f'twitchTokensFile argument is malformed: \"{twitchTokensFile}\"')

        self.__oauth2TokenUrl = oauth2TokenUrl
        self.__oauth2ValidateUrl = oauth2ValidateUrl
        self.__twitchTokensFile = twitchTokensFile

    def getAccessToken(self) -> str:
        jsonContents = self.__readJson()
        accessToken = jsonContents['accessToken']

        if not utils.isValidStr(accessToken):
            raise ValueError(f'\"accessToken\" value in \"{self.__twitchTokensFile}\" is malformed: \"{accessToken}\"')

        return accessToken

    def getRefreshToken(self) -> str:
        jsonContents = self.__readJson()
        refreshToken = jsonContents['refreshToken']

        if not utils.isValidStr(refreshToken):
            raise ValueError(f'\"refreshToken\" value in \"{self.__twitchTokensFile}\" is malformed: \"{refreshToken}\"')

        return refreshToken

    def __readJson(self) -> Dict:
        if not os.path.exists(self.__twitchTokensFile):
            raise FileNotFoundError(f'Twitch tokens file not found: \"{self.__twitchTokensFile}\"')

        with open(self.__twitchTokensFile, 'r') as file:
            jsonContents = json.load(file)

        if jsonContents is None:
            raise IOError(f'Error reading from Twitch tokens file: \"{self.__twitchTokensFile}\"')
        elif len(jsonContents) == 0:
            raise ValueError(f'JSON contents of Twitch tokens file \"{self.__twitchTokensFile}\" is empty')

        return jsonContents

    def __refreshTokens(
        self,
        twitchClientId: str,
        twitchClientSecret: str
    ):
        if not utils.isValidStr(twitchClientId):
            raise ValueError(f'twitchClientId argument is malformed: \"{twitchClientId}\"')
        elif not utils.isValidStr(twitchClientSecret):
            raise ValueError(f'twitchClientSecret argument is malformed: \"{twitchClientSecret}\"')

        rawResponse = None
        try:
            rawResponse = requests.post(
                url = self.__oauth2TokenUrl,
                params = {
                    'client_id': twitchClientId,
                    'client_secret': twitchClientSecret,
                    'grant_type': 'refresh_token',
                    'refresh_token': self.getRefreshToken()
                },
                timeout = utils.getDefaultTimeout()
            )
        except (ConnectionError, HTTPError, MaxRetryError, NewConnectionError, Timeout) as e:
            print(f'Exception occurred when attempting to request new Twitch tokens: {e}')
            raise RuntimeError(f'Exception occurred when attempting to request new Twitch tokens: {e}')

        jsonResponse = None
        try:
            jsonResponse = rawResponse.json()
        except JSONDecodeError as e:
            print(f'Exception occurred when attempting to decode new Twitch tokens response into JSON: {e}')
            raise RuntimeError(f'Exception occurred when attempting to decode new Twitch tokens response into JSON: {e}')

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

    def validateAndRefreshAccessToken(
        self,
        twitchClientId: str,
        twitchClientSecret: str
    ):
        if not utils.isValidStr(twitchClientId):
            raise ValueError(f'twitchClientId argument is malformed: \"{twitchClientId}\"')
        elif not utils.isValidStr(twitchClientSecret):
            raise ValueError(f'twitchClientSecret argument is malformed: \"{twitchClientSecret}\"')

        print(f'Validating Twitch access token... ({utils.getNowTimeText(includeSeconds = True)})')

        rawResponse = None
        try:
            rawResponse = requests.get(
                url = self.__oauth2ValidateUrl,
                params = {
                    'Authorization': f'OAuth {self.getAccessToken()}'
                },
                timeout = utils.getDefaultTimeout()
            )
        except (ConnectionError, HTTPError, MaxRetryError, NewConnectionError, Timeout) as e:
            print(f'Exception occurred when attempting to validate Twitch access token: {e}')
            raise RuntimeError(f'Exception occurred when attempting to validate Twitch access token: {e}')

        jsonResponse = None
        try:
            jsonResponse = rawResponse.json()
        except JSONDecodeError as e:
            print(f'Exception occurred when attempting to decode Twitch\'s response into JSON: {e}')
            raise RuntimeError(f'Exception occurred when attempting to decode Twitch\'s response into JSON: {e}')

        if jsonResponse.get('client_id') is None or len(jsonResponse['client_id']) == 0:
            print(f'Requesting new Twitch tokens... ({utils.getNowTimeText(includeSeconds = True)})')

            self.__refreshTokens(
                twitchClientId = twitchClientId,
                twitchClientSecret = twitchClientSecret
            )
        else:
            print(f'No need to request new Twitch tokens ({utils.getNowTimeText(includeSeconds = True)})')
