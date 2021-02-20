from CynanBotCommon.backingDatabase import BackingDatabase
from user import User

class AnalogueAnnounceChannelsRepository():

    def __init__(self, backingDatabase: BackingDatabase):
        if backingDatabase is None:
            raise ValueError(f'backingDatabase argument is malformed: \"{backingDatabase}\"')


