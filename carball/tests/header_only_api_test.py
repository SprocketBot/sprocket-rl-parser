from pathlib import Path

import carball


def get_short_sample_replay() -> str:
    return str(Path(__file__).resolve().parent / "replays" / "SHORT_SAMPLE.replay")


def test_header_only_api_skips_network_frames():
    replay_path = get_short_sample_replay()

    header_only = carball.decompile_replay_header_only(replay_path)

    assert isinstance(header_only, dict)
    assert "properties" in header_only
    assert header_only.get("network_frames") in (None, [])


def test_summarize_replay_file_matches_header_only_api():
    replay_path = get_short_sample_replay()

    assert carball.summarize_replay_file(replay_path) == carball.decompile_replay_header_only(replay_path)
