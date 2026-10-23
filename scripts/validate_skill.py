#!/usr/bin/env python3
"""Validate the frontmatter and local references in a skill directory."""

from __future__ import annotations

import argparse
import json
import math
import re
import stat
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

__all__ = ["validate_skill"]

ALLOWED_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
BLOCK_SCALARS = {">", ">-", "|", "|-"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
XML_TAG_PATTERN = re.compile(r"<[^<>\s][^<>]*>")
KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
MARKDOWN_LINK_START_PATTERN = re.compile(r"!?\[[^\]]*\]\(")
PLAIN_SCALAR_START = frozenset("[]{}>|*&!%@`'\"#")
NON_STRING_PLAIN_SCALARS = frozenset({"true", "false", "yes", "no", "on", "off", "null", "~"})
NON_STRING_PLAIN_SCALAR_PATTERNS = (
    re.compile(r"^[-+]?(\d[\d_]*(\.\d*)?|\.\d+)([eE][-+]?\d+)?$"),
    re.compile(r"^0x[0-9a-fA-F]+$"),
    re.compile(r"^0o[0-7]+$"),
    re.compile(r"^[-+]?\.(inf|Inf|INF)$"),
    re.compile(r"^\.(nan|NaN|NAN)$"),
)


def _message(path: Path, text: str, line_number: int | None = None) -> str:
    location = f"{path}:{line_number}" if line_number is not None else str(path)
    return f"{location}: {text}"


def _split_key_value(
    line: str,
    path: Path,
    line_number: int,
    errors: list[str],
) -> tuple[str, str] | None:
    match = KEY_PATTERN.fullmatch(line)
    if match is None:
        errors.append(_message(path, "frontmatter line is not a key: value pair", line_number))
        return None
    key, raw_value = match.groups()
    if raw_value and not raw_value[0].isspace():
        errors.append(
            _message(path, "frontmatter requires a space after the key colon", line_number)
        )
        return None
    return key, raw_value.strip()


def _parse_scalar(
    raw_value: str,
    path: Path,
    line_number: int,
    errors: list[str],
) -> str | None:
    if raw_value.startswith("'"):
        if len(raw_value) < 2 or not raw_value.endswith("'"):
            errors.append(_message(path, "single-quoted scalar is not closed", line_number))
            return None
        characters: list[str] = []
        index = 1
        end = len(raw_value) - 1
        while index < end:
            character = raw_value[index]
            if character == "'":
                if index + 1 >= end or raw_value[index + 1] != "'":
                    errors.append(
                        _message(path, "single quotes inside a scalar must be doubled", line_number)
                    )
                    return None
                characters.append("'")
                index += 2
            else:
                characters.append(character)
                index += 1
        return "".join(characters)

    if raw_value.startswith('"'):
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            errors.append(_message(path, "double-quoted scalar is not valid", line_number))
            return None
        if not isinstance(value, str):
            errors.append(_message(path, "quoted scalar must be a string", line_number))
            return None
        return value

    if raw_value and raw_value[0] in PLAIN_SCALAR_START:
        errors.append(_message(path, "plain scalar starts with a reserved character", line_number))
        return None
    if raw_value.casefold() in NON_STRING_PLAIN_SCALARS or any(
        pattern.fullmatch(raw_value) for pattern in NON_STRING_PLAIN_SCALAR_PATTERNS
    ):
        errors.append(_message(path, "plain scalar is not a string; quote it", line_number))
        return None
    if ": " in raw_value or " #" in raw_value:
        errors.append(_message(path, "plain scalar contains a reserved YAML sequence", line_number))
        return None
    return raw_value


def _read_block_scalar(
    lines: list[str],
    start: int,
    parent_indent: int,
    style: str,
    path: Path,
) -> tuple[str, int]:
    content_lines: list[str] = []
    content_indent: int | None = None
    index = start

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            content_lines.append("")
            index += 1
            continue
        if line.startswith("\t"):
            break
        indentation = len(line) - len(line.lstrip(" "))
        if indentation <= parent_indent:
            break
        if content_indent is None:
            content_indent = indentation
        if indentation < content_indent:
            break
        content_lines.append(line[content_indent:])
        index += 1

    while content_lines and not content_lines[-1]:
        content_lines.pop()

    value = "\n".join(content_lines)
    if style.startswith(">"):
        value = re.sub(r"(?<!\n)\n(?!\n)", " ", value)
    if content_lines and not style.endswith("-"):
        value += "\n"
    return value, index


def _parse_metadata(
    lines: list[str],
    start: int,
    path: Path,
    errors: list[str],
) -> tuple[dict[str, str], int]:
    metadata: dict[str, str] = {}
    base_indent: int | None = None
    index = start

    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip(" ").startswith("#"):
            index += 1
            continue
        if line.startswith("\t"):
            errors.append(_message(path, "metadata indentation must use spaces", index + 1))
            index += 1
            continue
        indentation = len(line) - len(line.lstrip(" "))
        if indentation == 0:
            break
        if base_indent is None:
            base_indent = indentation
        if indentation < base_indent:
            break
        if indentation > base_indent:
            errors.append(_message(path, "metadata values cannot be nested", index + 1))
            index += 1
            continue

        parsed = _split_key_value(line[base_indent:], path, index + 1, errors)
        if parsed is None:
            index += 1
            continue
        key, raw_value = parsed
        if key in metadata:
            errors.append(_message(path, f"duplicate metadata key {key!r}", index + 1))

        if raw_value in BLOCK_SCALARS:
            value, next_index = _read_block_scalar(
                lines,
                index + 1,
                base_indent,
                raw_value,
                path,
            )
        else:
            value = _parse_scalar(raw_value, path, index + 1, errors)
            next_index = index + 1
        if value is not None and key not in metadata:
            metadata[key] = value
        index = next_index

    return metadata, index


def _parse_frontmatter(
    lines: list[str],
    path: Path,
) -> tuple[dict[str, object], list[str]]:
    values: dict[str, object] = {}
    errors: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip(" ").startswith("#"):
            index += 1
            continue
        if line.startswith("\t") or line.startswith(" "):
            errors.append(_message(path, "unexpected indentation in frontmatter", index + 1))
            index += 1
            continue

        parsed = _split_key_value(line, path, index + 1, errors)
        if parsed is None:
            index += 1
            continue
        key, raw_value = parsed
        if key in values:
            errors.append(_message(path, f"duplicate frontmatter key {key!r}", index + 1))

        if key == "metadata" and not raw_value:
            value, next_index = _parse_metadata(lines, index + 1, path, errors)
        elif raw_value in BLOCK_SCALARS:
            value, next_index = _read_block_scalar(
                lines,
                index + 1,
                0,
                raw_value,
                path,
            )
        else:
            value = _parse_scalar(raw_value, path, index + 1, errors)
            next_index = index + 1

        if value is not None and key not in values:
            values[key] = value
        index = next_index

    return values, errors


def _validate_frontmatter(
    values: dict[str, object],
    skill_dir: Path,
    path: Path,
    errors: list[str],
    warnings: list[str],
) -> None:
    for key in sorted(values.keys() - ALLOWED_KEYS):
        errors.append(_message(path, f"unknown frontmatter key {key!r}"))

    name = values.get("name")
    if not isinstance(name, str):
        errors.append(_message(path, "name is required and must be a string"))
    else:
        if not 1 <= len(name) <= 64:
            errors.append(_message(path, "name must contain 1 to 64 characters"))
        if not NAME_PATTERN.fullmatch(name):
            errors.append(_message(path, "name must match ^[a-z0-9]+(-[a-z0-9]+)*$"))
        if "anthropic" in name or "claude" in name:
            errors.append(_message(path, "name must not contain anthropic or claude"))
        if name != skill_dir.name:
            errors.append(_message(path, "name must equal the skill directory name"))
        if XML_TAG_PATTERN.search(name):
            errors.append(_message(path, "name must not contain XML tags"))

    description = values.get("description")
    if not isinstance(description, str):
        errors.append(_message(path, "description is required and must be a string"))
    else:
        if not description.strip():
            errors.append(_message(path, "description must not be empty"))
        if len(description) > 1024:
            errors.append(_message(path, "description must not exceed 1024 characters"))
        if len(description) > 200:
            warnings.append(
                _message(
                    path,
                    f"description is {len(description)} characters; "
                    "claude.ai custom-skill upload allows 200",
                )
            )
        if XML_TAG_PATTERN.search(description):
            errors.append(_message(path, "description must not contain XML tags"))

    compatibility = values.get("compatibility")
    if compatibility is not None and (
        not isinstance(compatibility, str) or not 1 <= len(compatibility) <= 500
    ):
        errors.append(_message(path, "compatibility must contain 1 to 500 characters"))

    metadata = values.get("metadata")
    if metadata is not None and (
        not isinstance(metadata, dict)
        or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in metadata.items()
        )
    ):
        errors.append(_message(path, "metadata must be a mapping of strings to strings"))

    for key in ("license", "allowed-tools"):
        value = values.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(_message(path, f"{key} must be a non-empty string"))


def _skip_link_title(markdown: str, index: int) -> int:
    if index >= len(markdown) or markdown[index] not in {"'", '"', "("}:
        return index

    delimiter = markdown[index]
    if delimiter in {"'", '"'}:
        index += 1
        while index < len(markdown):
            if markdown[index] == "\\" and index + 1 < len(markdown):
                index += 2
            elif markdown[index] == delimiter:
                return index + 1
            else:
                index += 1
        return index

    depth = 1
    index += 1
    while index < len(markdown):
        if markdown[index] == "\\" and index + 1 < len(markdown):
            index += 2
        elif markdown[index] == "(":
            depth += 1
            index += 1
        elif markdown[index] == ")":
            depth -= 1
            index += 1
            if depth == 0:
                return index
        else:
            index += 1
    return index


def _link_targets(markdown: str) -> list[str]:
    targets: list[str] = []
    position = 0
    while match := MARKDOWN_LINK_START_PATTERN.search(markdown, position):
        index = match.end()
        while index < len(markdown) and markdown[index].isspace():
            index += 1
        if index == len(markdown):
            position = match.end()
            continue

        if markdown[index] == "<":
            end = markdown.find(">", index + 1)
            if end == -1:
                position = match.end()
                continue
            target = markdown[index + 1 : end]
            destination_end = end + 1
        else:
            target_characters: list[str] = []
            parenthesis_depth = 0
            while index < len(markdown):
                character = markdown[index]
                if character == "\\" and index + 1 < len(markdown):
                    target_characters.append(markdown[index + 1])
                    index += 2
                    continue
                if character.isspace():
                    break
                if character == "(":
                    parenthesis_depth += 1
                elif character == ")":
                    if parenthesis_depth == 0:
                        break
                    parenthesis_depth -= 1
                target_characters.append(character)
                index += 1
            target = "".join(target_characters)
            destination_end = index

        if target:
            targets.append(target)

        title_end = destination_end
        while title_end < len(markdown) and markdown[title_end].isspace():
            title_end += 1
        title_end = _skip_link_title(markdown, title_end)
        while title_end < len(markdown) and markdown[title_end].isspace():
            title_end += 1
        position = (
            title_end + 1
            if title_end < len(markdown) and markdown[title_end] == ")"
            else destination_end
        )
    return targets


def _is_ignored_link(target: str) -> bool:
    if target.startswith("#") or target.startswith("//") or target.startswith("/"):
        return True
    return urlsplit(target).scheme.lower() in {"http", "https", "mailto"}


def _resolve_link(
    target: str,
    source: Path,
    skill_root: Path,
    errors: list[str],
) -> Path | None:
    try:
        ignored_link = _is_ignored_link(target)
    except ValueError:
        errors.append(_message(source, f"link target {target!r} is not a valid URL"))
        return None
    if ignored_link:
        return None
    path_target = unquote(target.split("#", 1)[0])
    if not path_target:
        errors.append(_message(source, f"link target {target!r} is empty"))
        return None

    candidate = source.parent / path_target
    try:
        resolved = candidate.resolve()
        resolved.relative_to(skill_root.resolve())
    except (OSError, RuntimeError, ValueError):
        errors.append(
            _message(
                source, f"relative link target {target!r} must stay inside the skill directory"
            )
        )
        return None
    if not resolved.is_file():
        errors.append(_message(source, f"relative link target {target!r} must exist as a file"))
        return None
    return resolved


def _validate_links(skill_dir: Path, body: str, skill_file: Path, errors: list[str]) -> None:
    skill_root = skill_dir.resolve()
    referenced_markdown: set[Path] = set()

    for target in _link_targets(body):
        path = _resolve_link(target, skill_file, skill_root, errors)
        if path is not None and path.suffix.lower() == ".md":
            referenced_markdown.add(path)

    for path in sorted(referenced_markdown):
        try:
            markdown = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append(_message(path, "referenced Markdown file could not be read"))
            continue
        for target in _link_targets(markdown):
            try:
                ignored_link = _is_ignored_link(target)
            except ValueError:
                errors.append(_message(path, f"link target {target!r} is not a valid URL"))
                continue
            if not ignored_link:
                errors.append(
                    _message(
                        path,
                        "referenced Markdown files must not link to other local files",
                    )
                )
                break


def validate_skill(skill_dir: Path) -> tuple[list[str], list[str]]:
    """Return validation errors and warnings for one skill directory."""
    errors: list[str] = []
    warnings: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    if skill_dir.is_symlink():
        errors.append(_message(skill_file, "skill directory must not be a symlink"))
        return errors, warnings
    if not skill_dir.is_dir():
        errors.append(_message(skill_file, "skill directory must exist and be a directory"))
        return errors, warnings
    if skill_file.is_symlink():
        errors.append(_message(skill_file, "SKILL.md must not be a symlink"))
        return errors, warnings
    try:
        if not stat.S_ISREG(skill_file.lstat().st_mode):
            errors.append(_message(skill_file, "SKILL.md must be a regular file"))
            return errors, warnings
        text = skill_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(_message(skill_file, "SKILL.md is missing"))
        return errors, warnings
    except (OSError, UnicodeError) as exc:
        errors.append(_message(skill_file, f"SKILL.md could not be read: {exc}"))
        return errors, warnings

    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = normalized_text.splitlines(keepends=True)
    lines = [line.removesuffix("\n") for line in raw_lines]
    if not lines or lines[0] != "---":
        errors.append(_message(skill_file, "frontmatter must start with a --- line"))
        return errors, warnings

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line == "---"),
        None,
    )
    if closing_index is None:
        errors.append(_message(skill_file, "frontmatter must have a closing --- line"))
        return errors, warnings

    frontmatter, parse_errors = _parse_frontmatter(lines[1:closing_index], skill_file)
    errors.extend(parse_errors)
    _validate_frontmatter(frontmatter, skill_dir, skill_file, errors, warnings)

    body = "".join(raw_lines[closing_index + 1 :])
    body_lines = body.splitlines()
    if len(body_lines) > 500:
        errors.append(_message(skill_file, "body must not exceed 500 lines"))
    estimated_tokens = math.ceil(len(body) / 4)
    if estimated_tokens > 5000:
        errors.append(
            _message(
                skill_file,
                f"body estimates to {estimated_tokens} tokens using "
                "ceil(len(body) / 4); limit is 5000",
            )
        )
    _validate_links(skill_dir, body, skill_file, errors)
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directories", metavar="DIR", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = False

    for directory in args.directories:
        errors, warnings = validate_skill(directory)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        if errors:
            failed = True
        else:
            print(f"OK: {directory}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
