#!/usr/bin/env python3
"""
Prints a concise summary of a Rocket League replay.

Usage:
    python scripts/replay_summary.py path/to/match.replay

The script relies on :mod:`carball` to parse the replay and uses the JSON output to emit
the final score, team assignment, and the headline stats for every player.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from carball.decompile_replays import analyze_replay_file

TEAM_NAME = {True: "Orange", False: "Blue"}  # type: Mapping[bool, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize score and player stats for a Rocket League replay.",
    )
    parser.add_argument(
        "replay",
        type=Path,
        help="Path to a Rocket League `.replay` file.",
    )
    parser.add_argument(
        "--calculate-intensive-events",
        action="store_true",
        help="Enable the heavier stats calculations in carball.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip replay cleanup after parsing (more raw output).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only log errors from carball; useful when parsing many files.",
    )
    return parser.parse_args()


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "Unknown"
    total_seconds = int(round(seconds))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes}m{secs:02d}s"


def format_timestamp(value: str | None) -> str:
    if not value:
        return "Unknown"
    try:
        # Some replays store the timestamp as a stringified int.
        ts = int(value)
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except ValueError:
        return value


def _resolve_player_id(player: Mapping[str, Any]) -> str:
    player_id = player.get("id")
    if isinstance(player_id, Mapping):
        return str(player_id.get("id") or player_id.get("online_id") or "unknown")
    return str(player_id or "unknown")


def _get_player_platform(player: Mapping[str, Any]) -> str:
    return player.get("platform") or "unknown platform"


def summarize_teams(metadata: Mapping[str, Any], teams: Iterable[Mapping[str, Any]]) -> Mapping[str, int]:
    scoreboard: dict[str, int] = {}
    for team in teams:
        color = TEAM_NAME.get(bool(team.get("isOrange")), "Orange")
        scoreboard[color] = int(team.get("score") or 0)

    if scoreboard:
        return scoreboard

    fallback = metadata.get("score") or {}
    scoreboard["Blue"] = int(fallback.get("team0Score") or 0)
    scoreboard["Orange"] = int(fallback.get("team1Score") or 0)
    return scoreboard


def print_replay_summary(json_data: Mapping[str, Any], replay_path: Path) -> None:
    metadata = json_data.get("gameMetadata", {})
    print(f"Replay: {replay_path}")
    print(f"Name  : {metadata.get('name', 'Unknown')}")
    print(f"Map   : {metadata.get('map', 'Unknown')}")
    print(f"Match : {metadata.get('matchGuid', 'Unknown')}")
    print(f"Server: {metadata.get('serverName', 'Unknown')} ({metadata.get('gameServerId', 'Unknown ID')})")
    print(f"Playlist: {metadata.get('playlist', 'Unknown')}")
    print(f"Started : {format_timestamp(metadata.get('time'))}")
    print(f"Duration: {format_duration(metadata.get('length'))}")
    team_size = metadata.get("teamSize")
    if team_size is not None:
        print(f"Team Size: {team_size}")

    teams = list(json_data.get("teams", []))
    scoreboard = summarize_teams(metadata, teams)
    if scoreboard:
        blue_score = scoreboard.get("Blue", 0)
        orange_score = scoreboard.get("Orange", 0)
        print(f"Score: Blue {blue_score} – Orange {orange_score}")
    else:
        print("Score: Unknown")

    players = list(json_data.get("players", []))
    if not players:
        print("No player data available.")
        return

    print("\nPlayers:")
    for color in ("Blue", "Orange"):
        team_players = [p for p in players if bool(p.get("isOrange")) == (color == "Orange")]
        if not team_players:
            continue

        team_score = next(
            (team.get("score") for team in teams if bool(team.get("isOrange")) == (color == "Orange")),
            scoreboard.get(color, 0),
        )
        print(f"  {color} Team (Score: {team_score}):")
        for player in team_players:
            pid = _resolve_player_id(player)
            platform = _get_player_platform(player)
            name = player.get("name") or pid
            goals = player.get("goals", 0)
            assists = player.get("assists", 0)
            saves = player.get("saves", 0)
            shots = player.get("shots", 0)
            points = player.get("score", 0)
            print(
                f"    {name} ({platform}, ID {pid}) – "
                f"Goals {goals} / Assists {assists} / Saves {saves} / Shots {shots} / Points {points}"
            )


def main() -> None:
    args = parse_args()
    replay_path = args.replay
    if not replay_path.exists():
        raise SystemExit(f"Replay not found: {replay_path}")

    logging_level = logging.ERROR if args.quiet else logging.NOTSET

    analysis = analyze_replay_file(
        str(replay_path),
        calculate_intensive_events=args.calculate_intensive_events,
        clean=not args.no_clean,
        logging_level=logging_level,
    )

    json_data = analysis.get_json_data()
    print_replay_summary(json_data, replay_path)


if __name__ == "__main__":
    main()
