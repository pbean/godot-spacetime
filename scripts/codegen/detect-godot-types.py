#!/usr/bin/env python3
"""
detect-godot-types.py

Post-processor for SpacetimeDB C# codegen.
Scans *.g.cs files in a Types/ directory, detects structs whose field
layouts match Godot built-in types (Vector2, Vector3, etc.), and writes
companion *.godot.g.cs files with implicit conversion operators.

Usage:
    python3 detect-godot-types.py <path/to/Types/>

Exit codes:
    0 — success (even if no layouts matched)
    1 — fatal error (I/O failure, argument error)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Layout definitions
# ---------------------------------------------------------------------------

# Each entry: (godot_type, field_type, field_names, name_filter)
# name_filter: callable(class_name) -> bool | None (always match when None)
LAYOUTS: list[tuple[str, str, list[str], object]] = [
    ("Vector2",    "float", ["X", "Y"],          None),
    ("Vector3",    "float", ["X", "Y", "Z"],      None),
    ("Vector4",    "float", ["X", "Y", "Z", "W"], lambda n: "quat" not in n.lower()),
    ("Quaternion", "float", ["X", "Y", "Z", "W"], lambda n: "quat" in n.lower()),
    ("Color",      "float", ["R", "G", "B", "A"], None),
    ("Vector2I",   "int",   ["X", "Y"],           None),
    ("Vector3I",   "int",   ["X", "Y", "Z"],      None),
    ("Vector4I",   "int",   ["X", "Y", "Z", "W"], None),
]

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_FIELD_RE = re.compile(
    r"^\s*public\s+(?!static\b)(?!const\b)(?!readonly\b)"
    r"([A-Za-z_][\w:.<>\?\[\],]*)\s+(\w+)\s*;"
)
_CLASS_RE = re.compile(r"public\s+sealed\s+partial\s+class\s+(\w+)")


class ParseError(RuntimeError):
    """Raised when an annotated generated type cannot be parsed safely."""


def parse_class(
    source: str, *, source_name: str = "<memory>"
) -> tuple[str, list[tuple[str, str]]] | None:
    """
    Parse a .g.cs source for a [SpacetimeDB.Type]-annotated sealed partial class.

    Returns (class_name, [(field_type, field_name), ...]) or None if not found.
    All public instance fields are returned so layout validation can reject
    mixed or extra fields instead of silently ignoring them.
    """
    lines = source.splitlines()
    class_name: str | None = None
    fields: list[tuple[str, str]] = []
    in_class = False
    found_stdb_type = False
    saw_stdb_type = False
    class_line_no: int | None = None
    brace_depth = 0

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Track [SpacetimeDB.Type] annotation
        if "[SpacetimeDB.Type]" in stripped:
            found_stdb_type = True
            saw_stdb_type = True
            continue

        # Find class declaration after the annotation
        if found_stdb_type and not in_class:
            m = _CLASS_RE.search(stripped)
            if m:
                class_name = m.group(1)
                class_line_no = line_no
                in_class = True
                brace_depth = stripped.count("{") - stripped.count("}")
                continue
            # Only reset if we hit a non-attribute, non-comment, non-blank line
            if (
                stripped
                and not stripped.startswith("[")
                and not stripped.startswith("//")
                and not stripped.startswith("/*")
                and not stripped.startswith("*")
            ):
                raise ParseError(
                    f"{source_name}:{line_no}: [SpacetimeDB.Type] must be followed by "
                    "a 'public sealed partial class' declaration"
                )
            continue

        if in_class:
            brace_depth += stripped.count("{") - stripped.count("}")

            # Skip attribute lines and blank lines
            if stripped.startswith("[") or not stripped:
                continue

            # Handle lines containing braces (constructors, methods, etc.)
            if "{" in stripped or "}" in stripped:
                if brace_depth <= 0:
                    break  # class body ended
                continue

            # Attempt to match a public instance field. We intentionally keep
            # unsupported types so detect_layout() can reject mixed/extra fields.
            m = _FIELD_RE.match(line)
            if m:
                fields.append((m.group(1), m.group(2)))

    if in_class and class_name is not None and brace_depth > 0:
        raise ParseError(
            f"{source_name}:{class_line_no}: unterminated class body for '{class_name}'"
        )

    if saw_stdb_type and class_name is None:
        raise ParseError(
            f"{source_name}: [SpacetimeDB.Type] was found, but no supported class declaration was parsed"
        )

    if class_name is not None:
        return class_name, fields
    return None


# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------

def detect_layout(class_name: str, fields: list[tuple[str, str]]) -> str | None:
    """Return the Godot type name if fields match a known layout, else None."""
    for godot_type, field_type, field_names, name_filter in LAYOUTS:
        if len(fields) != len(field_names):
            continue
        if all(
            ft == field_type and fn == en
            for (ft, fn), en in zip(fields, field_names)
        ):
            if name_filter is None or name_filter(class_name):
                return godot_type
    return None


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def _field_args(fields: list[tuple[str, str]]) -> str:
    """Return comma-separated 'v.FieldName' args for all fields."""
    return ", ".join(f"v.{fn}" for _, fn in fields)


def generate_companion(
    class_name: str, godot_type: str, fields: list[tuple[str, str]]
) -> str:
    """Return the full content of a .godot.g.cs companion file."""
    fa = _field_args(fields)
    return (
        "// THIS FILE IS AUTOMATICALLY GENERATED BY detect-godot-types (godot-spacetime codegen).\n"
        "// EDITS TO THIS FILE WILL NOT BE SAVED."
        " Regenerate with: bash scripts/codegen/generate-smoke-test.sh\n"
        "\n"
        "#nullable enable\n"
        "\n"
        "using Godot;\n"
        "\n"
        "namespace SpacetimeDB.Types\n"
        "{\n"
        f"    public sealed partial class {class_name}\n"
        "    {\n"
        f"        /// <summary>Implicitly convert to Godot.{godot_type}.</summary>\n"
        f"        public static implicit operator {godot_type}({class_name} v) => new {godot_type}({fa});\n"
        "\n"
        f"        /// <summary>Implicitly convert from Godot.{godot_type}.</summary>\n"
        f"        public static implicit operator {class_name}({godot_type} v) => new {class_name}({fa});\n"
        "    }\n"
        "}\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/Types/>", file=sys.stderr)
        return 1

    types_dir = Path(sys.argv[1])
    if not types_dir.is_dir():
        print(f"Error: '{types_dir}' is not a directory", file=sys.stderr)
        return 1

    mappings: list[tuple[str, str, list[tuple[str, str]]]] = []

    # Process each .g.cs file that is not itself a companion
    for source_file in sorted(types_dir.glob("*.g.cs")):
        if source_file.name.endswith(".godot.g.cs"):
            continue

        try:
            source = source_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Error reading '{source_file}': {exc}", file=sys.stderr)
            return 1

        try:
            result = parse_class(source, source_name=str(source_file))
        except ParseError as exc:
            print(f"Error parsing '{source_file}': {exc}", file=sys.stderr)
            return 1

        if result is None:
            continue

        class_name, fields = result
        godot_type = detect_layout(class_name, fields)
        if godot_type is None:
            continue

        mappings.append((class_name, godot_type, fields))

    desired_companions = {
        types_dir / f"{class_name}.godot.g.cs" for class_name, _, _ in mappings
    }

    # Idempotency: clean up stale companions only after the full parse succeeds.
    for stale in types_dir.glob("*.godot.g.cs"):
        if stale in desired_companions:
            continue
        try:
            stale.unlink()
        except OSError as exc:
            print(f"Error removing stale companion '{stale}': {exc}", file=sys.stderr)
            return 1

    for class_name, godot_type, fields in mappings:
        companion_path = types_dir / f"{class_name}.godot.g.cs"
        content = generate_companion(class_name, godot_type, fields)
        try:
            companion_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            print(f"Error writing '{companion_path}': {exc}", file=sys.stderr)
            return 1

        print(f"  \u2192 {class_name} ({godot_type}) \u2014 companion written")

    return 0


if __name__ == "__main__":
    sys.exit(main())
