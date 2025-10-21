#!/usr/bin/env python3
"""Builds a gitleaks config file from optional inline contents, template variables, and extend flag."""
import argparse
import json
import sys
from pathlib import Path
import string
from typing import Iterable


class ConfigBuildError(Exception):
    """Raised when the config cannot be built due to invalid user input."""

def read_strip(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def build_config(*, template_path: Path, inline_contents: str, vars_json: str, extend: bool) -> str:
    sections = []

    if extend:
        print('Adding extend block to configuration')
        sections.append("[extend]\nuseDefault = true")

    contents = inline_contents.strip()
    if contents:
        print('Inline config contents detected')
        sections.append(contents)

    vars_raw = vars_json.strip()
    if vars_raw:
        print('Template variables supplied for substitution')
        try:
            data = json.loads(vars_raw)
        except json.JSONDecodeError as exc:
            raise ConfigBuildError(f"Invalid JSON in gitleaks_config_vars: {exc}") from exc

        template_text = template_path.read_text(encoding="utf-8")
        template = string.Template(template_text)
        try:
            rendered = template.substitute(data).strip()
        except KeyError as exc:
            raise ConfigBuildError(f"Missing template value for key: {exc.args[0]}") from exc

        if rendered:
            print('Applied template variables to configuration')
            sections.append(rendered)

    if not sections:
        print('No configuration sections produced')
        return ""

    print('Configuration composed successfully')
    return "\n\n".join(sections) + "\n"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Path to write the combined config")
    parser.add_argument("--template", required=True, help="Template TOML file for variable substitution")
    parser.add_argument("--contents", required=False, help="File containing inline config contents")
    parser.add_argument("--vars", required=False, help="File containing JSON variables for substitution")
    parser.add_argument("--extend", required=False, default="false", help="Whether to prepend the extend block")
    return parser.parse_args(argv)


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    template_path = Path(args.template)
    inline_contents = read_strip(Path(args.contents)) if args.contents else ""
    vars_json = read_strip(Path(args.vars)) if args.vars else ""
    extend_flag = str(args.extend).lower() == "true"

    print('Executing config builder CLI')

    try:
        config_text = build_config(
            template_path=template_path,
            inline_contents=inline_contents,
            vars_json=vars_json,
            extend=extend_flag,
        )
    except ConfigBuildError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output)

    if config_text:
        output_path.write_text(config_text, encoding="utf-8")
        print('Generated config file written to disk')
    else:
        if output_path.exists():
            output_path.unlink()
            print('Existing config file removed because no content was generated')
        else:
            print('No custom config generated; nothing written')

    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
