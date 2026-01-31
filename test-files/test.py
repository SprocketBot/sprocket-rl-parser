import json
from pathlib import Path

import carball

filenames = [
    'arzeniclelarod_wafflessquashy_5-4',
    'squashyarzenic_waffles_lelarod_3-4',
    'wafflesarzenic_lelarodsquashy_3-4',
]

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"


def resolve_replay_path(name: str) -> Path:
    path = BASE_DIR / name
    if path.exists():
        return path
    replay_path = BASE_DIR / f"{name}.replay"
    if replay_path.exists():
        return replay_path
    raise FileNotFoundError(f"Replay not found: {name}")


def write_json_to_file(path: Path, json_data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_data, indent=2))


def get_player_stats_with_zero_id(raw_json):
    stats = raw_json.get("properties", {}).get("PlayerStats", [])
    zero_id_players = []
    for player in stats:
        online_id = player.get("OnlineID")
        if online_id in ("0", 0, None):
            player_id = player.get("PlayerID", {}).get("fields", {})
            zero_id_players.append(
                {
                    "name": player.get("Name"),
                    "online_id": online_id,
                    "player_id_fields": player_id,
                }
            )
    return zero_id_players


def get_processed_player_id_map(processed_json):
    result = {}
    for player in processed_json.get("players", []):
        name = player.get("name")
        player_id = player.get("id", {}).get("id")
        if name is not None:
            result[name] = player_id
    return result


def assert_processed_players_have_ids_and_platforms(processed_json, replay_name: str):
    missing = []
    for player in processed_json.get("players", []):
        name = player.get("name")
        player_id = player.get("id", {}).get("id")
        platform = player.get("platform")
        if not player_id or not platform:
            missing.append(
                {
                    "name": name,
                    "id": player_id,
                    "platform": platform,
                }
            )
    if missing:
        raise AssertionError(
            f"Missing player id/platform in {replay_name}: {missing}"
        )


for i, name in enumerate(filenames):
    replay_path = resolve_replay_path(name)
    raw_decomp = carball.decompile_replay(str(replay_path))
    full_anal = carball.analyze_replay_file(str(replay_path))

    write_json_to_file(OUTPUT_DIR / f"raw_out_{i}.json", raw_decomp)
    processed_json = full_anal.get_json_data()
    write_json_to_file(OUTPUT_DIR / f"processed_{i}.json", processed_json)
    assert_processed_players_have_ids_and_platforms(processed_json, replay_path.name)

    zero_id_players = get_player_stats_with_zero_id(raw_decomp)
    if zero_id_players:
        processed_map = get_processed_player_id_map(processed_json)
        print(f"Replay {replay_path.name} has zero OnlineID in PlayerStats:")
        for player in zero_id_players:
            name = player["name"]
            player_id_fields = player["player_id_fields"]
            processed_id = processed_map.get(name)
            print(
                f"  - {name}: PlayerID fields={player_id_fields} | processed id={processed_id}"
            )
    
