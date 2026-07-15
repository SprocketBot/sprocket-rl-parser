import json
import logging
import os
from collections import Counter
from typing import Callable, IO

from google.protobuf.json_format import _Printer

from ..generated.api import game_pb2
from .saltie_game.metadata.ApiGoal import ApiGoal
from .saltie_game.metadata.ApiPlayer import ApiPlayer
from .saltie_game.metadata.ApiTeam import ApiTeam
from .utils.json_encoder import CarballJsonEncoder
from .utils.proto_manager import ProtobufManager
from ..json_parser.game import Game

script_path = os.path.abspath(__file__)
with open(os.path.join(os.path.dirname(script_path), 'PROTOBUF_VERSION'), 'r') as f:
    PROTOBUF_VERSION = json.loads(f.read())

logger = logging.getLogger(__name__)


class SummaryManager:
    """
    Builds protobuf/json metadata from replay header data only.
    """

    def __init__(self, game: Game):
        self.game = game
        self.protobuf_game = game_pb2.Game()
        self.protobuf_game.version = PROTOBUF_VERSION
        self.id_creator = self._create_player_id_function(game)

    def create_summary(self):
        metadata = self.protobuf_game.game_metadata
        metadata.id = self.game.id
        if self.game.name is not None:
            metadata.name = str(self.game.name)
        metadata.map = self.game.map
        if self.game.replay_version is not None:
            metadata.version = self.game.replay_version
        if self.game.datetime is not None:
            metadata.time = int(self.game.datetime.timestamp())
        metadata.frames = max((goal.frame_number for goal in self.game.goals), default=0)
        metadata.team_size = self.game.team_size
        metadata.is_invalid_analysis = True
        metadata.match_guid = self.game.id

        for team in self.game.teams:
            if team.is_orange:
                metadata.score.team_1_score = team.score or 0
            else:
                metadata.score.team_0_score = team.score or 0

        if self.game.primary_player is not None and self.game.primary_player['id'] is not None:
            metadata.primary_player.id = str(self.game.primary_player['id'])

        for player in self.game.players:
            player_proto = self.protobuf_game.players.add()
            ApiPlayer.create_from_player(player_proto, player, self.id_creator)

        ApiTeam.create_teams_from_game(self.game, self.protobuf_game, self.id_creator)
        ApiGoal.create_goals_from_game(self.game, metadata.goals, self.id_creator)

    def write_json_out_to_file(self, file: IO):
        if 'b' in file.mode:
            raise IOError('Json files can not be binary use open(path,"w")')
        json.dump(self.get_json_data(), file, indent=2, cls=CarballJsonEncoder)

    def write_proto_out_to_file(self, file: IO):
        if 'b' not in file.mode:
            raise IOError('Proto files must be binary use open(path,"wb")')
        ProtobufManager.write_proto_out_to_file(file, self.protobuf_game)

    def get_protobuf_data(self) -> game_pb2.Game:
        return self.protobuf_game

    def get_json_data(self):
        printer = _Printer()
        return printer._MessageToJsonObject(self.protobuf_game)

    def get_data_frame(self):
        raise NotImplementedError("Summary parsing does not include frame data")

    def _create_player_id_function(self, game: Game) -> Callable:
        name_map = {}
        for player in game.players:
            player_id = player.online_id
            if player_id in (None, ""):
                logger.warning(
                    "Player is missing a stable header id; falling back to name: %s",
                    player.name,
                )
                player_id = player.name
            name_map[player.name] = player_id

        dupes = {
            name: [p.online_id for p in game.players if p.name == name]
            for name, count in Counter(player.name for player in game.players).items()
            if count > 1
        }
        if dupes:
            logger.warning(
                "Duplicate player names detected in summary parsing; id mapping by name will overwrite: %s",
                dupes,
            )

        def create_name(proto_player_id, name):
            value = name_map.get(name, name)
            proto_player_id.id = str(value)

        return create_name
