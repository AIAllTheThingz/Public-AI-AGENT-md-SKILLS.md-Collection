#!/usr/bin/env python3
"""Check source-review metadata and report fresh, stale, and not-run review state without network access."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402

TOOL = "check-freshness"
VERSION = "1.0.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = "SOURCE_REVIEWS.json"
FORMAT_VERSION = "1.0.0"
ALLOWED_MATURITY = {"planned", "draft", "baseline", "stable", "deprecated"}
MAINTENANCE_FINDING_CODES = {"SOURCE_REVIEW_STALE", "SOURCE_REVIEW_NOT_RUN"}


def parse_as_of(value: str | None) -> date:
    if value is None:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("--as-of must use YYYY-MM-DD format") from exc


def resolve_registry(root: Path, raw: str) -> tuple[Path, str]:
    relative = Path(raw)
    if relative.is_absolute():
        raise ValueError("--registry must be a repository-relative path")

    repository_root = root.resolve()
    resolved = (repository_root / relative).resolve()
    try:
        resolved.relative_to(repository_root)
    except ValueError as exc:
        raise ValueError("--registry must resolve inside the repository root") from exc

    if not resolved.is_file():
        raise FileNotFoundError(f"Source-review registry not found: {relative.as_posix()}")
    return resolved, relative.as_posix()


def safe_scope(
    root: Path,
    raw: Any,
    record_id: str,
    registry: str,
    findings: list[Finding],
) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        findings.append(Finding(
            "SOURCE_REVIEW_SCOPE_INVALID",
            f"Record {record_id!r} must declare a non-empty repository-relative scope.",
            path=registry,
        ))
        return None

    relative = Path(raw.strip())
    if relative.is_absolute():
        findings.append(Finding(
            "SOURCE_REVIEW_SCOPE_INVALID",
            f"Record {record_id!r} scope must be repository-relative: {raw}",
            path=registry,
        ))
        return None

    repository_root = root.resolve()
    resolved = (repository_root / relative).resolve()
    try:
        resolved.relative_to(repository_root)
    except ValueError:
        findings.append(Finding(
            "SOURCE_REVIEW_SCOPE_ESCAPES_ROOT",
            f"Record {record_id!r} scope resolves outside the repository root: {raw}",
            path=registry,
        ))
        return None

    if not resolved.exists():
        findings.append(Finding(
            "SOURCE_REVIEW_SCOPE_MISSING",
            f"Record {record_id!r} scope does not exist: {raw}",
            path=registry,
        ))
        return None
    return relative.as_posix()


def validate_sources(
    raw: Any,
    record_id: str,
    registry: str,
    findings: list[Finding],
) -> int:
    if not isinstance(raw, list) or not raw:
        findings.append(Finding(
            "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_MISSING",
            f"Record {record_id!r} must declare at least one authoritative source.",
            path=registry,
        ))
        return 0

    valid = 0
    for index, source in enumerate(raw):
        if not isinstance(source, dict):
            findings.append(Finding(
                "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_INVALID",
                f"Record {record_id!r} source {index} must be an object.",
                path=registry,
            ))
            continue
        name = source.get("name")
        url = source.get("url")
        if not isinstance(name, str) or not name.strip():
            findings.append(Finding(
                "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_INVALID",
                f"Record {record_id!r} source {index} must have a non-empty name.",
                path=registry,
            ))
            continue
        if not isinstance(url, str):
            findings.append(Finding(
                "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_INVALID",
                f"Record {record_id!r} source {index} must use an absolute HTTPS URL.",
                path=registry,
            ))
            continue
        parsed = urlsplit(url)
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            findings.append(Finding(
                "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_INVALID",
                f"Record {record_id!r} source {index} must use an absolute HTTPS URL.",
                path=registry,
            ))
            continue
        valid += 1
    return valid


def review_date_state(
    raw: Any,
    *,
    record_id: str,
    interval_days: int,
    as_of: date,
    strict: bool,
    registry: str,
    findings: list[Finding],
) -> tuple[str, date | None, date | None, int | None]:
    severity = "error" if strict else "warning"
    if raw is None:
        findings.append(Finding(
            "SOURCE_REVIEW_NOT_RUN",
            f"Authoritative-source review has not been recorded for {record_id}.",
            severity=severity,
            path=registry,
            details={"state": "NotRun", "asOf": as_of.isoformat()},
        ))
        return "NotRun", None, None, None

    if not isinstance(raw, str):
        findings.append(Finding(
            "SOURCE_REVIEW_DATE_INVALID",
            f"Record {record_id!r} lastReviewed must be null or YYYY-MM-DD.",
            path=registry,
        ))
        return "Invalid", None, None, None

    try:
        reviewed = date.fromisoformat(raw)
    except ValueError:
        findings.append(Finding(
            "SOURCE_REVIEW_DATE_INVALID",
            f"Record {record_id!r} lastReviewed must use YYYY-MM-DD: {raw!r}.",
            path=registry,
        ))
        return "Invalid", None, None, None

    if reviewed > as_of:
        findings.append(Finding(
            "SOURCE_REVIEW_DATE_FUTURE",
            f"Record {record_id!r} lastReviewed is after the evaluation date: {reviewed.isoformat()}.",
            path=registry,
        ))
        return "Invalid", reviewed, None, None

    due = reviewed + timedelta(days=interval_days)
    age_days = (as_of - reviewed).days
    if as_of > due:
        findings.append(Finding(
            "SOURCE_REVIEW_STALE",
            f"Authoritative-source review is stale for {record_id}; reviewed {reviewed.isoformat()}, due {due.isoformat()}.",
            severity=severity,
            path=registry,
            details={
                "state": "Warning",
                "lastReviewed": reviewed.isoformat(),
                "dueOn": due.isoformat(),
                "ageDays": age_days,
                "reviewIntervalDays": interval_days,
            },
        ))
        return "Warning", reviewed, due, age_days

    return "Passed", reviewed, due, age_days


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    registry_path, registry = resolve_registry(root, args.registry)

    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Source-review registry must contain a JSON object")
    if data.get("formatVersion") != FORMAT_VERSION:
        raise ValueError(f"{registry} formatVersion must be {FORMAT_VERSION}")

    as_of = parse_as_of(args.as_of)
    findings: list[Finding] = []
    records = data.get("records")
    if not isinstance(records, list) or not records:
        findings.append(Finding(
            "SOURCE_REVIEW_RECORDS_MISSING",
            "Source-review registry must contain at least one record.",
            path=registry,
        ))
        records = []

    default_interval = data.get("defaultReviewIntervalDays", 180)
    if not isinstance(default_interval, int) or isinstance(default_interval, bool) or not 1 <= default_interval <= 3650:
        findings.append(Finding(
            "SOURCE_REVIEW_INTERVAL_INVALID",
            "defaultReviewIntervalDays must be an integer between 1 and 3650.",
            path=registry,
        ))
        default_interval = 180

    seen: set[str] = set()
    evaluated: list[dict[str, Any]] = []
    counts = {"Passed": 0, "Warning": 0, "NotRun": 0, "Invalid": 0}
    authoritative_sources = 0

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            findings.append(Finding(
                "SOURCE_REVIEW_RECORD_INVALID",
                f"Record {index} must be an object.",
                path=registry,
            ))
            counts["Invalid"] += 1
            continue

        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            findings.append(Finding(
                "SOURCE_REVIEW_ID_INVALID",
                f"Record {index} must declare a non-empty id.",
                path=registry,
            ))
            counts["Invalid"] += 1
            continue
        record_id = record_id.strip()
        if record_id in seen:
            findings.append(Finding(
                "SOURCE_REVIEW_ID_DUPLICATE",
                f"Duplicate source-review id: {record_id}",
                path=registry,
            ))
            counts["Invalid"] += 1
            continue
        seen.add(record_id)

        scope = safe_scope(root, record.get("scope"), record_id, registry, findings)
        maturity = record.get("maturity")
        if maturity is not None and maturity not in ALLOWED_MATURITY:
            findings.append(Finding(
                "SOURCE_REVIEW_MATURITY_INVALID",
                f"Record {record_id!r} uses unsupported maturity state: {maturity!r}.",
                path=registry,
            ))

        interval = record.get("reviewIntervalDays", default_interval)
        if not isinstance(interval, int) or isinstance(interval, bool) or not 1 <= interval <= 3650:
            findings.append(Finding(
                "SOURCE_REVIEW_INTERVAL_INVALID",
                f"Record {record_id!r} reviewIntervalDays must be an integer between 1 and 3650.",
                path=registry,
            ))
            interval = default_interval

        authoritative_sources += validate_sources(record.get("authoritativeSources"), record_id, registry, findings)
        state, reviewed, due, age_days = review_date_state(
            record.get("lastReviewed"),
            record_id=record_id,
            interval_days=interval,
            as_of=as_of,
            strict=args.strict,
            registry=registry,
            findings=findings,
        )
        counts[state] = counts.get(state, 0) + 1
        evaluated.append({
            "id": record_id,
            "scope": scope,
            "maturity": maturity,
            "state": state,
            "lastReviewed": reviewed.isoformat() if reviewed else None,
            "dueOn": due.isoformat() if due else None,
            "ageDays": age_days,
            "reviewIntervalDays": interval,
        })

    has_structural_errors = any(
        item.severity == "error" and item.code not in MAINTENANCE_FINDING_CODES
        for item in findings
    )
    if has_structural_errors:
        freshness_state = "Invalid"
    elif counts["Warning"]:
        freshness_state = "Warning"
    elif counts["NotRun"]:
        freshness_state = "NotRun"
    else:
        freshness_state = "Passed"

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "freshnessState": freshness_state,
            "asOf": as_of.isoformat(),
            "records": len(records),
            "passed": counts["Passed"],
            "warnings": counts["Warning"],
            "notRun": counts["NotRun"],
            "invalid": counts["Invalid"],
            "authoritativeSources": authoritative_sources,
            "strict": args.strict,
            "liveSourceVerification": "NotRun",
            "findings": len(findings),
        },
        metadata={
            "registry": registry,
            "networkAccess": "NotRun; this tool is intentionally offline",
            "records": evaluated,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY,
        help=f"Repository-relative source-review registry path. Default: {DEFAULT_REGISTRY}",
    )
    parser.add_argument(
        "--as-of",
        help="Evaluate review age as of YYYY-MM-DD. Defaults to the current date.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat stale or not-run source reviews as errors instead of warnings.",
    )
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
