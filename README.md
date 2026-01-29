# sprocket-rl-parser
An open-source project for decompiling and analyzing Rocket League replays.

## Install
`pip install sprocket-rl-parser`

## Usage
```python
import parser
analysis_manager = parser.analyze_replay_file('replay.replay')
proto_game = analysis_manager.get_protobuf_data()
```