import hashlib
import logging

bots = [
    # Alap Rocket League botok
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

    # Saját / egyedi botnevek
    "cyberdash",
    "A7mber",
    "AHS77",
    "Aroxen",
    "Arvian",
    "Aryxie",
    "Astro",
    "Bl4ze",
    "Blaze000",
    "BlazeTom",
    "Blitz",
    "BruzlyRL",
    "BUGzilla",
    "Byte",
    "Cherry69",
    "Code_0101",
    "cosmo",
    "Csigusz",
    "D3monix",
    "Dani4l_R",
    "DarkN1ght",
    "DarkNeo",
    "Data11",
    "echo1strike",
    "enter1",
    "Error",
    "Ex0tiik",
    "ferrox",
    "Finch1",
    "Fl4re",
    "Flash",
    "Flixor",
    "FluxerZ",
    "FluxRider",
    "Frost",
    "ghost",
    "H3XXEN",
    "H4nnah",
    "Hanna22",
    "herkedavid",
    "HEXA",
    "HuntedXX",
    "Ignixx",
    "inferno",
    "JadeFox",
    "Jet_99",
    "JetPack",
    "K1RO",
    "Kael",
    "Kairo",
    "Kavreen",
    "KCintia01",
    "kilobyte",
    "knoxlevi",
    "kroniqzero",
    "KRYLON07",
    "L3oShot",
    "Laggosaur",
    "Leaf777",
    "Liam03",
    "Loonix",
    "LunaVee",
    "Lynx",
    "Mavr1k",
    "Maxon007",
    "Munch",
    "N8Rider",
    "Nebyra",
    "NeoClash1",
    "Nexari",
    "Nitr0",
    "Noobster",
    "Nova_21",
    "NovaByte",
    "NoxxRider",
    "Nyx",
    "Onyx_74",
    "OrbitX",
    "OrionZ",
    "OXY",
    "PixelDrift",
    "Plasma",
    "polarix",
    "Poppy_Pop",
    "Prime11",
    "pulse99",
    "PulseV",
    "Qube",
    "R3Lix",
    "Raven09",
    "Ravex",
    "RazenOne",
    "Reaper",
    "rekta",
    "Rift00",
    "Riven7",
    "Rocket_Nate",
    "RogueLin",
    "ryd3r",
    "Rynox",
    "Shad0w",
    "Sky8",
    "SkyeBird",
    "Solven",
    "Sophie7",
    "spark",
    "speedmarie",
    "stellar_kick",
    "Steynixx",
    "Strike",
    "Stryke9",
    "Syncra",
    "Talon",
    "Talvorn",
    "Tazm0",
    "Tessa_3",
    "thrashZZZ",
    "thunder_thalia_11",
    "Titaan",
    "TORQ",
    "Tox1k",
    "Trixal",
    "Trixy",
    "unit",
    "v0idrider",
    "V4lkan",
    "v4tara",
    "vayro_12",
    "Velmor",
    "Ven0m",
    "Vex",
    "vexlucas",
    "Vexrail",
    "Vitrix",
    "Void",
    "Volt4ce",
    "Vorniik",
    "Vortex7",
    "Wyrm",
    "Z0ne",
    "Zephyx",
    "Zephyyyr8",
    "Zer0",
]

logger = logging.getLogger(__name__)


def h11(w):
    if isinstance(w, str):
        w = w.encode("utf-8")
    return hashlib.md5(w).hexdigest()[:9]


def normalize_bot_name(name):
    """
    Normalizálja a nevet:
    - trim
    - ha ilyen: '(ADR) FluxerZ' -> 'FluxerZ'
    - ha ilyen: '[ADR] FluxerZ' -> 'FluxerZ'
    - több space -> egy space
    """
    raw_name = str(name or "").strip()

    if not raw_name:
        return ""

    cleaned_name = raw_name

    # Zárójeles csapat prefix levágása: "(ADR) FluxerZ"
    if cleaned_name.startswith("(") and ")" in cleaned_name:
        cleaned_name = cleaned_name.split(")", 1)[1].strip()

    # Szögletes zárójeles prefix levágása: "[ADR] FluxerZ"
    if cleaned_name.startswith("[") and "]" in cleaned_name:
        cleaned_name = cleaned_name.split("]", 1)[1].strip()

    # Többszörös space-ek normalizálása
    cleaned_name = " ".join(cleaned_name.split())

    return cleaned_name


def get_bot_map():
    result = {}
    for i in range(len(bots)):
        result[bots[i]] = i + 1
    return result


def get_online_id_for_bot(bot_map, player):
    logger.warning("Generating bot id for player flagged as bot: name=%s", player.name)

    raw_name = str(player.name or "").strip()
    cleaned_name = normalize_bot_name(raw_name)

    # 1. próbáljuk az eredeti nevet
    try:
        return "b" + str(bot_map[raw_name]) + "b"
    except Exception:
        pass

    # 2. próbáljuk a tisztított nevet
    try:
        return "b" + str(bot_map[cleaned_name]) + "b"
    except Exception:
        logger.warning(
            "Unknown bot name encountered, using fallback bot id instead of failing. raw_name=%s cleaned_name=%s",
            raw_name,
            cleaned_name
        )

        # 3. fallback ID, hogy sose álljon le a parser
        hash_source = cleaned_name or raw_name or "unknown_bot"
        fallback_hash = hashlib.sha1(hash_source.lower().encode("utf-8")).hexdigest()[:12]
        return f"fallback_bot_{fallback_hash}"
