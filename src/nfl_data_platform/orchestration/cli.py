"""CLI entry points for the NFL data platform."""

from __future__ import annotations

import argparse
from pathlib import Path

from nfl_data_platform.config import Settings, get_settings
from nfl_data_platform.orchestration.pipeline import (
    PipelineRunContext,
    initialize_database,
    run_phase1_pipeline,
)


def _build_settings(args: argparse.Namespace) -> Settings:
    """Build settings, allowing CLI overrides for common replay parameters."""
    settings = get_settings()
    seasons = (args.season,) if args.season else settings.nflverse_seasons
    return Settings(
        environment=settings.environment,
        database_url=settings.database_url,
        nflverse_seasons=seasons,
        nflverse_data_dir=settings.nflverse_data_dir,
        temp_data_dir=settings.temp_data_dir,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""
    parser = argparse.ArgumentParser(prog="nfl-data-platform")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db = subparsers.add_parser("init-db")
    init_db.add_argument("--season", type=int)
    init_db.add_argument("--week", type=int)
    init_db.add_argument("--season-type", default="REG")
    init_db.add_argument("--full-refresh", action="store_true")

    run_phase1 = subparsers.add_parser("run-phase1")
    run_phase1.add_argument("--season", type=int)
    run_phase1.add_argument("--week", type=int)
    run_phase1.add_argument("--season-type", default="REG")
    run_phase1.add_argument("--full-refresh", action="store_true")
    return parser


def main() -> int:
    """Run the requested CLI command."""
    parser = build_parser()
    args = parser.parse_args()
    settings = _build_settings(args)
    context = PipelineRunContext(
        season=args.season,
        week=args.week,
        season_type=args.season_type,
        full_refresh=args.full_refresh,
    )

    if args.command == "init-db":
        result = initialize_database(settings)
        ddl_dir = Path("sql/ddl")
        ddl_files = sorted(path.name for path in ddl_dir.glob("*.sql"))
        print(f"Database status: {result['status']}")
        print(f"DDL files: {', '.join(ddl_files)}")
        return 0

    if args.command == "run-phase1":
        result = run_phase1_pipeline(settings, context=context)
        quality_count = len(result["quality_results"])
        print(f"Phase 1 pipeline completed with {quality_count} quality check results.")
        print(f"CSV output directory: {result['run_output_dir']}")
        print(result["load_status"])
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 1
