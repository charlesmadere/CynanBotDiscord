from twitchAccounceSettingsHelper import TwitchAnnounceUser


class TwitchLiveHelper():

    def __init__(self):
        pass

    def isLive(user: TwitchAnnounceUser) -> bool:
        if user is None:
            raise ValueError(f'user argument is malformed: \"{user}\"')

        # TODO

        return False
