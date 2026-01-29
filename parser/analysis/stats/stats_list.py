from typing import List

from parser.analysis.stats.demos.demos import DemoStat
from parser.analysis.stats.dribbles.ball_carry import CarryStat
from parser.analysis.stats.kickoffs.kickoff_stat import KickoffStat
from parser.analysis.stats.possession.per_possession import PerPossessionStat
from parser.analysis.stats.ball_forward.distance_hit_ball_forward import DistanceStats
from parser.analysis.stats.boost.boost import BoostStat
from parser.analysis.stats.controls.controls import ControlsStat
from parser.analysis.stats.possession.ball_distances import BallDistanceStat
from parser.analysis.stats.possession.possession import PossessionStat
from parser.analysis.stats.possession.turnovers import TurnoverStat
from parser.analysis.stats.stats import BaseStat, HitStat
from parser.analysis.stats.tendencies.averages import Averages
from parser.analysis.stats.tendencies.hit_counts import HitCountStat
from parser.analysis.stats.tendencies.positional_tendencies import PositionalTendencies
from parser.analysis.stats.tendencies.relative_position_tendencies import RelativeTendencies
from parser.analysis.stats.tendencies.speed_tendencies import SpeedTendencies
from parser.analysis.stats.tendencies.team_tendencies import TeamTendencies
from parser.analysis.stats.rumble.rumble import RumbleItemStat
from parser.analysis.stats.rumble.goals import PreRumbleGoals, ItemGoals
from parser.analysis.stats.dropshot.goals import DropshotGoals
from parser.analysis.stats.dropshot.ball_phase_times import DropshotBallPhaseTimes
from parser.analysis.stats.dropshot.damage import DropshotStats


class StatsList:
    """
    Where you add any extra stats you want calculated.
    """

    @staticmethod
    def get_player_stats() -> List[BaseStat]:
        """These are stats that end up being assigned to a specific player"""
        return [BoostStat(),
                PositionalTendencies(),
                Averages(),
                BallDistanceStat(),
                ControlsStat(),
                SpeedTendencies(),
                CarryStat(),
                PerPossessionStat(),
                SpeedTendencies(),
                RumbleItemStat(),
                KickoffStat(),
                DropshotStats(),
                DemoStat()
                ]

    @staticmethod
    def get_team_stats() -> List[BaseStat]:
        """These are stats that end up being assigned to a specific team"""
        return [PossessionStat(),
                TeamTendencies(),
                RelativeTendencies(),
                PerPossessionStat(),
                RumbleItemStat(),
                PreRumbleGoals(),
                DropshotStats()
                ]

    @staticmethod
    def get_general_stats() ->List[BaseStat]:
        """These are stats that end up being assigned to the game as a whole"""
        return [PositionalTendencies(),
                SpeedTendencies(),
                ItemGoals(),
                DropshotGoals(),
                DropshotBallPhaseTimes(),
                DropshotStats()
                ]

    @staticmethod
    def get_hit_stats() ->List[HitStat]:
        """These are stats that depend on current hit and next hit"""
        return [DistanceStats(),
                PossessionStat(),
                HitCountStat(),
                TurnoverStat()
                ]
