# sprocket-rl-parser
An open-source project for decompiling and analyzing Rocket League replays. It exposes a Python API that returns
protobuf metadata, JSON output, and a pandas DataFrame for frame-by-frame analysis.

## Install
```bash
pip install sprocket-rl-parser
```

## Quickstart (Python)
```python
import carball

analysis_manager = carball.analyze_replay_file("path/to/replay.replay")

# Protobuf game metadata + stats
proto_game = analysis_manager.get_protobuf_data()

# JSON-friendly dict
json_game = analysis_manager.get_json_data()

# Frame-by-frame data
data_frame = analysis_manager.get_data_frame()
```

If you only need replay metadata and want to avoid parsing network frames entirely:
```python
summary_manager = carball.summarize_replay_file("path/to/replay.replay")

# Protobuf metadata only
proto_game = summary_manager.get_protobuf_data()

# JSON-friendly dict without frame data
json_game = summary_manager.get_json_data()
```

## CLI
The package installs a `carball` command for one-off parsing.

```bash
carball --input path/to/replay.replay --json output.json --proto output.proto --gzip frames.gzip
```

## Output formats
### Protobuf
`analysis_manager.get_protobuf_data()` returns a `game_pb2.Game` object. This is the authoritative metadata and stats
output (players, teams, events, goals, etc.). The schema lives under `api/` in this repo.

### JSON
`analysis_manager.get_json_data()` returns a JSON-compatible dict matching the protobuf schema. Use
`analysis_manager.write_json_out_to_file()` to persist the output.

### DataFrame (frame-by-frame)
`analysis_manager.get_data_frame()` returns a pandas DataFrame with a MultiIndex column structure:

- The index is the sequential frame number.
- Columns are tuples like `(object, field)` where `object` is `game`, `ball`, or a player name.

Example: pull ball positions and a single player's positions.
```python
ball = data_frame["ball"][["pos_x", "pos_y", "pos_z"]]
player = data_frame["SomePlayerName"][["pos_x", "pos_y", "pos_z"]]
```

You can also persist the DataFrame with gzip and read it back:
```python
import gzip
from carball.analysis.utils.pandas_manager import PandasManager

with gzip.open("frames.gzip", "wb") as f:
    analysis_manager.write_pandas_out_to_file(f)

with gzip.open("frames.gzip", "rb") as f:
    df = PandasManager.read_numpy_from_memory(f)
```

## Advanced options
`analyze_replay_file` supports additional flags:

- `analysis_per_goal=True` to analyze each goal segment independently.
- `calculate_intensive_events=True` for extra stats that are more expensive to compute.
- `clean=False` to skip data cleanup if you want rawer frame data.

```python
analysis_manager = carball.analyze_replay_file(
    "path/to/replay.replay",
    analysis_per_goal=False,
    calculate_intensive_events=True,
    clean=True,
)
```

## Troubleshooting
- If you see missing or invalid data, try `calculate_intensive_events=False` and `clean=True` first.
- For reproducible analysis, make sure you are parsing the raw `.replay` file and not a previously decompiled JSON.
- If a replay no longer has parsable network frames after a game update, use `summarize_replay_file()` or
  `decompile_replay_header_only()` for header-only parsing.
