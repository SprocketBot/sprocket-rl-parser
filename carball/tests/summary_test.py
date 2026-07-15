from copy import deepcopy
from pathlib import Path

import pytest

import carball
from carball.decompile_replays import analyze_replay_file
from carball.json_parser.game import Game


def get_modern_replay_path() -> str:
    return str(
        Path(__file__).resolve().parents[2]
        / "test-files/psn-ids/2026-01-31.12.57 DubiousDugger Private Win 2026-01-31-12-57.replay"
    )


def get_identity_parity_replay_paths():
    root = Path(__file__).resolve().parents[2]
    return [
        root / "test-files/psn-ids/2026-01-31.12.57 DubiousDugger Private Win 2026-01-31-12-57.replay",
        root / "test-files/xbox-ids/172a7141a9c2aae47f3111149ef66951a9ea5631b2750a164696fde1e9a65a50.replay",
        root / "carball/tests/replays/crossplatform_party.replay",
        root / "carball/tests/replays/PLAY_STATION_ONLY_PARTY.replay",
    ]


def get_player_identity_map(game_json):
    return {
        player["name"]: {
            "id": player.get("id", {}).get("id"),
            "platform": player.get("platform"),
        }
        for player in game_json.get("players", [])
    }


def get_team_identity_map(game_json):
    return {
        team.get("isOrange"): sorted(player_id.get("id") for player_id in team.get("playerIds", []))
        for team in game_json.get("teams", [])
    }


def get_goal_scorer_ids(game_json):
    return [
        goal.get("playerId", {}).get("id")
        for goal in game_json.get("gameMetadata", {}).get("goals", [])
    ]


def test_decompile_replay_header_only_skips_network_frames():
    replay_json = carball.decompile_replay_header_only(get_modern_replay_path())
    assert replay_json.get("network_frames") is None
    assert len(replay_json["properties"]["PlayerStats"]) == 4


def test_game_initialize_summary_does_not_require_network_frames():
    replay_json = carball.decompile_replay(get_modern_replay_path())
    replay_json = deepcopy(replay_json)
    replay_json.pop("network_frames")

    game = Game()
    game.initialize(loaded_json=replay_json, parse_replay=False)

    assert len(game.players) == 4
    assert len(game.goals) == 4
    assert game.frames is None
    assert len(game.teams) == 2


def test_summarize_replay_file_returns_metadata_without_frames():
    summary = carball.summarize_replay_file(get_modern_replay_path())
    proto = summary.get_protobuf_data()

    assert proto.game_metadata.id
    assert proto.game_metadata.is_invalid_analysis is True
    assert len(proto.players) == 4
    assert len(proto.teams) == 2
    with pytest.raises(NotImplementedError):
        summary.get_data_frame()


def test_analyze_replay_file_requires_network_frames(monkeypatch):
    replay_json = carball.decompile_replay(get_modern_replay_path())
    replay_json = deepcopy(replay_json)
    replay_json["network_frames"] = None

    monkeypatch.setattr(
        "carball.decompile_replays.decompile_replay",
        lambda _: deepcopy(replay_json),
    )

    with pytest.raises(ValueError, match="summarize_replay_file"):
        analyze_replay_file(get_modern_replay_path())


@pytest.mark.parametrize("replay_path", get_identity_parity_replay_paths())
def test_summary_identity_matches_full_analysis_when_playerstats_exist(replay_path):
    summary_json = carball.summarize_replay_file(str(replay_path)).get_json_data()
    full_json = carball.analyze_replay_file(str(replay_path)).get_json_data()

    assert get_player_identity_map(summary_json) == get_player_identity_map(full_json)
    assert get_team_identity_map(summary_json) == get_team_identity_map(full_json)
    assert get_goal_scorer_ids(summary_json) == get_goal_scorer_ids(full_json)
