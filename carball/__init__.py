try:
    from .decompile_replays import decompile_replay
    from .decompile_replays import decompile_replay_header_only
    from .decompile_replays import analyze_replay_file
    from .decompile_replays import summarize_replay_file
except ModuleNotFoundError as e:
    print("Not importing functions due to missing packages:", e)
