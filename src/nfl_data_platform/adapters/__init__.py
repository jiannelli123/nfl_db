"""Source adapters for NFL data providers."""

from nfl_data_platform.adapters.base import BaseSourceAdapter
from nfl_data_platform.adapters.nflverse import NFLVerseAdapter

__all__ = ["BaseSourceAdapter", "NFLVerseAdapter"]
