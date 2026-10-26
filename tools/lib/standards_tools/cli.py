"""Shared command-line behavior."""

from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path
from typing import Callable

from .models import ToolResult
from .reporting import emit_result


def add_common_arguments(parser: argparse.ArgumentParser, *, default_root: Path) -> None:
    parser.add_argument(
        "--root",
        type=Path,
        default=default_root,
        help="Repository root to inspect. Defaults to the repository containing this tool.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
        help="Result output format.",
    )
    parser.add_argument("--output", type=Path, help="Optional file for the rendered result.")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout output.")


def require_date_time_format(format_checker: object) -> None:
    """Stop when jsonschema lacks its optional date-time checker, which otherwise accepts any string."""
    if format_checker.conforms("not-a-date", "date-time"):
        raise SystemExit(
            "Missing dependency 'rfc3339-validator': jsonschema would accept any date-time value. Install with: "
            "python -m pip install -r tools/validate-schemas/requirements.txt"
        )


def execute_tool(
    *,
    tool: str,
    version: str,
    parser: argparse.ArgumentParser,
    run: Callable[[argparse.Namespace], ToolResult],
    argv: list[str] | None = None,
) -> int:
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except (ValueError, FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        result = ToolResult.error(tool=tool, version=version, message=str(exc), code="INPUT_ERROR")
        exit_code = 2
    except Exception as exc:  # noqa: BLE001 - CLI boundary converts unexpected failures
        result = ToolResult.error(tool=tool, version=version, message=str(exc), code="INTERNAL_ERROR")
        result.metadata["exceptionType"] = type(exc).__name__
        if getattr(args, "debug", False):
            result.metadata["traceback"] = traceback.format_exc()
        exit_code = 3
    else:
        exit_code = result.exit_code()

    emit_result(
        result,
        output_format=args.output_format,
        output=args.output,
        quiet=args.quiet,
    )
    return exit_code
