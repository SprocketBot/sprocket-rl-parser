import hashlib
import logging

bots = [
    "Armstrong",
    "Bandit",
    "Beast",
    "Boomer",
    "Buzz",
    "Casper",
    "Caveman",
    "C-Block",
    "Centice",
    "Chipper",
    "Cougar",
    "Dude",
    "Foamer",
    "Fury",
    "Gerwin",
    "Goose",
    "Heater",
    "Hollywood",
    "Hound",
    "Iceman",
    "Imp",
    "Jester",
    "JM",
    "Junker",
    "Khan",
    "Maverick",
    "Middy",
    "Merlin",
    "Mountain",
    "Myrtle",
    "Outlaw",
    "Poncho",
    "Rainmaker",
    "Raja",
    "Rex",
    "Roundhouse",
    "Sabretooth",
    "Saltie",
    "Samara",
    "Scout",
    "Shepard",
    "Slider",
    "Squall",
    "Sticks",
    "Stinger",
    "Storm",
    "Sundown",
    "Sultan",
    "Swabbie",
    "Tusk",
    "Tex",
    "Viper",
    "Wolfman",
    "Yuri",
]

logger = logging.getLogger(__name__)


def h11(w):
    return hashlib.md5(w).hexdigest()[:9]


def get_bot_map():
    result = dict()
    for i in range(len(bots)):
        result[bots[i]] = i + 1
    return result


def get_online_id_for_bot(bot_map, player):
    logger.warning("Generating bot id for player flagged as bot: name=%s", player.name)
    try:
        return 'b' + str(bot_map[player.name]) + 'b'
    except:
        logger.error('Found bot not in bot list; refusing to hash name for id. bot_name=%s', player.name)
        raise ValueError(f"Bot name not in bot list: {player.name}")
