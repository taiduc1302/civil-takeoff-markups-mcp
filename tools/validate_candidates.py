"""Dependency-free validation of synthetic markup candidates before MCP payload generation.

This checks *structure*, not feature targeting or native Bluebeam measurement accuracy.
The fixture may be generated from the same variables as the drawing and is NOT
independent proof of PDF geometry extraction.
"""
from __future__ import annotations

import math
import re

GROUPS = ("runs", "resto", "points", "qa")
MOVE = re.compile(r"^M\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+|$)")
NUMBER = r"-?\d+(?:\.\d+)?"
COMMANDS = re.compile(r"[MLH]")
SUPPORTED_SCALE = re.compile(r"^1\s*mm\s*=\s*\d+(?:\.\d+)?\s*m$", re.I)
ALLOWED_UNITS = {"m", "m2", "ea"}


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("coordinate must be numeric") from None
    if not math.isfinite(number):
        raise ValueError("coordinate must be finite")
    return number


def parse_path(raw, closed=False):
    """Parse the deliberately small M/L/[H] grammar of the synthetic fixture."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("path must be a non-empty string")
    tokens = raw.split()
    if not tokens or tokens[0] != "M":
        raise ValueError("path must start with M")
    points = []
    idx = 0
    found_close = False
    while idx < len(tokens):
        command = tokens[idx]
        if command == "H":
            if idx != len(tokens) - 1 or found_close:
                raise ValueError("H must appear once at end")
            found_close = True
            idx += 1
            continue
        if command not in {"M", "L"} or (idx != 0 and command != "L"):
            raise ValueError("only first M then L coordinates and final H are supported")
        if idx + 2 >= len(tokens):
            raise ValueError("incomplete coordinate pair")
        x, y = _number(tokens[idx + 1]), _number(tokens[idx + 2])
        points.append((x, y))
        idx += 3
    if found_close != closed:
        raise ValueError("polygon closure mismatch")
    if len(points) < (3 if closed else 2):
        raise ValueError("insufficient path vertices")
    if len(set(points)) < (3 if closed else 2):
        raise ValueError("degenerate path")
    if closed:
        area2 = sum(
            points[i][0] * points[(i + 1) % len(points)][1]
            - points[(i + 1) % len(points)][0] * points[i][1]
            for i in range(len(points))
        )
        if abs(area2) < 1e-6:
            raise ValueError("zero-area polygon")
    return points


def validate_candidates(data, page=1):
    """Return human-readable errors, not a misleading approval decision."""
    errors = []
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        errors.append("page must be a positive 1-based integer")
    if not isinstance(data, dict):
        return errors + ["candidate root must be an object"]
    if not isinstance(data.get("scale"), str) or not SUPPORTED_SCALE.fullmatch(data["scale"].strip()):
        errors.append("invalid synthetic scale declaration")
    expected = {"runs": "m", "resto": "m2", "points": "ea", "qa": "m"}
    seen = set()
    for group in GROUPS:
        rows = data.get(group)
        if not isinstance(rows, list):
            errors.append(f"{group}: expected array")
            continue
        for index, row in enumerate(rows):
            context = f"{group}[{index}]"
            if not isinstance(row, dict):
                errors.append(f"{context}: expected object")
                continue
            id_ = row.get("id")
            if not isinstance(id_, str) or not id_.strip():
                errors.append(f"{context}: missing ID")
            elif id_ in seen:
                errors.append(f"{context}: duplicate ID {id_}")
            else:
                seen.add(id_)
            subject = row.get("subject")
            if not isinstance(subject, str) or not subject.strip():
                errors.append(f"{context}: missing subject")
            elif group == "qa" and not subject.startswith("QA CHECK - DO NOT SUM"):
                errors.append(f"{context}: QA markup must be DO NOT SUM")
            elif group != "qa" and "DO NOT SUM" in subject:
                errors.append(f"{context}: only QA group may use DO NOT SUM")
            if "unit" in row and row["unit"] not in ALLOWED_UNITS:
                errors.append(f"{context}: unsupported unit {row['unit']!r}")
            if "unit" in row and row["unit"] != expected[group]:
                errors.append(f"{context}: unexpected {group} unit {row['unit']!r}")
            try:
                if group == "points":
                    rect = row.get("rect")
                    coords = [_number(p) for p in rect.split()] if isinstance(rect, str) else []
                    if len(coords) != 4 or coords[2] <= 0 or coords[3] <= 0:
                        raise ValueError("rect requires finite x y width height with positive dimensions")
                    color = row.get("color")
                    if not isinstance(color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                        raise ValueError("invalid point color")
                else:
                    parse_path(row.get("path"), closed=group == "resto")
            except ValueError as exc:
                errors.append(f"{context}: {exc}")
    printed = data.get("printed")
    if not isinstance(printed, dict):
        errors.append("printed: expected schedule object")
    elif any(not isinstance(k, str) or not isinstance(v, (int, float)) or isinstance(v, bool)
             or not math.isfinite(v) or v < 0 for k, v in printed.items()):
        errors.append("printed: non-finite or invalid schedule quantity")
    return errors
