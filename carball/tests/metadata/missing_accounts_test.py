from collections import Counter
from pathlib import Path

import pytest

from carball.decompile_replays import analyze_replay_file, decompile_replay


MISSING_ACCOUNTS_DIR = Path(__file__).resolve().parents[3] / "test-files" / "missing-accounts"
MISSING_ACCOUNT_REPLAYS = sorted(MISSING_ACCOUNTS_DIR.glob("*.replay"))


@pytest.mark.skipif(not MISSING_ACCOUNT_REPLAYS, reason="No missing-accounts replay fixtures found.")
@pytest.mark.parametrize("replay_path", MISSING_ACCOUNT_REPLAYS, ids=lambda replay: replay.name)
def test_player_accounts_match_raw_player_stats(replay_path: Path):
    raw_replay = decompile_replay(str(replay_path))
    raw_player_stats = raw_replay.get("properties", {}).get("PlayerStats", [])
    raw_names = [player.get("Name") for player in raw_player_stats if player.get("Name")]

    analysis = analyze_replay_file(str(replay_path))
    parsed_names = [player.name for player in analysis.get_protobuf_data().players]

    missing_names = Counter(raw_names) - Counter(parsed_names)
    extra_names = Counter(parsed_names) - Counter(raw_names)

    assert not missing_names and not extra_names, (
        f"Replay {replay_path.name} dropped or changed players during parsing. "
        f"raw={raw_names}, parsed={parsed_names}, "
        f"missing={list(missing_names.elements())}, extra={list(extra_names.elements())}"
    )
