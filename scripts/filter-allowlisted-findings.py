#!/usr/bin/env python3
"""Retire an individual TruffleHog finding by fingerprint, and nothing wider.

TruffleHog has no baseline or ignore mechanism of its own: the levers it ships
are per-detector, per-path and per-entropy. All three are blunter than the
problem. A false positive in a *commit message* has no path at all, so it cannot
be scoped away, and turning a detector off repository-wide is exactly what this
action refuses to allow.

So the unit here is one finding. A fingerprint is the SHA-256 of the detector
name and the matched text, which is stable across runs and across commits - the
same string quoted in four commit messages is one fingerprint, not four - and
carries no location, so it does not churn when history is rewritten or a file
moves.

Two deliberate choices:

  The matched text is never printed. For a false positive it would be harmless,
  but this same path runs over real findings, and a log is a durable, widely
  readable place for a live credential to end up. The fingerprint, detector and
  location are enough to identify and triage one.

  Every entry must carry a reason, and an entry that matches nothing is
  reported. An allowlist nobody prunes becomes permanent blindness, and the
  failure is silent by nature: the entry stops corresponding to anything and
  keeps suppressing whatever it happens to match next.

Reads TruffleHog's JSON-lines output on stdin. Exits 0 when every finding is
allowlisted, 1 when any is not, and 2 when the allowlist itself is unusable -
a malformed allowlist must never read as "nothing to report".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")


def fingerprint(detector: str, raw: str) -> str:
    """Identify a finding by what it is, not where it was found."""
    return hashlib.sha256(f"{detector}\n{raw}".encode()).hexdigest()


def parse_allowlist(path: pathlib.Path) -> dict[str, str]:
    """Fingerprint -> reason. Raises ValueError on anything it cannot trust."""
    entries: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        parts = text.split(maxsplit=1)
        if not FINGERPRINT.match(parts[0]):
            raise ValueError(
                f"{path}:{number}: expected a 64-character hex fingerprint, got {parts[0]!r}. "
                "The fingerprint is printed beside every unallowlisted finding - copy it from there."
            )
        if len(parts) == 1 or not parts[1].strip():
            raise ValueError(
                f"{path}:{number}: fingerprint {parts[0][:12]}… has no reason. "
                "Every entry must say why it is here, or the next reader cannot judge it."
            )
        if parts[0] in entries:
            raise ValueError(f"{path}:{number}: fingerprint {parts[0][:12]}… is listed twice.")
        entries[parts[0]] = parts[1].strip()
    return entries


def location(finding: dict) -> str:
    """Where the finding was seen. Commit-message findings carry no file."""
    git = finding.get("SourceMetadata", {}).get("Data", {}).get("Git", {})
    commit = (git.get("commit") or "")[:8]
    path = git.get("file")
    where = f"{path}:{git.get('line', '?')}" if path else "commit message (no file)"
    return f"{where}  commit {commit}" if commit else where


def read_findings(stream) -> list[dict]:
    """One JSON object per line; TruffleHog also emits log lines, so skip those."""
    findings = []
    for line in stream:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("DetectorName"):
            findings.append(record)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allowlist", required=True, type=pathlib.Path)
    args = parser.parse_args()

    if not args.allowlist.is_file():
        print(
            f"::error::trufflehog_allowlist points at {args.allowlist}, which does not exist. "
            "Refusing to run rather than scanning with an allowlist nobody can read.",
            file=sys.stderr,
        )
        return 2

    try:
        allowed = parse_allowlist(args.allowlist)
    except (ValueError, OSError) as error:
        print(f"::error::{error}", file=sys.stderr)
        return 2

    findings = read_findings(sys.stdin)
    suppressed: dict[str, int] = {}
    remaining: list[dict] = []

    for finding in findings:
        key = fingerprint(finding["DetectorName"], finding.get("Raw", ""))
        if key in allowed:
            suppressed[key] = suppressed.get(key, 0) + 1
        else:
            remaining.append((key, finding))

    if suppressed:
        print(f"----- {sum(suppressed.values())} finding(s) retired by the allowlist -----")
        for key, count in suppressed.items():
            print(f"  {key[:16]}…  x{count}  {allowed[key]}")

    stale = sorted(set(allowed) - set(suppressed))
    if stale:
        print(f"----- {len(stale)} allowlist entry(ies) matched nothing -----")
        for key in stale:
            print(f"  {key[:16]}…  {allowed[key]}")
        print(
            "::warning::Some allowlist entries matched no finding. Either the false positive is "
            "gone and the entry should be deleted, or the thing it described has changed shape - "
            "both are worth a look, because a stale entry silently suppresses whatever it matches next."
        )

    if remaining:
        print(f"----- {len(remaining)} finding(s) NOT allowlisted -----")
        for key, finding in remaining:
            print(f"  {finding['DetectorName']}  {location(finding)}")
            print(f"    fingerprint: {key}")
        print(
            "::error::TruffleHog reported findings that are not in the allowlist. Treat each as real "
            "until shown otherwise. If one is a false positive, add its fingerprint above to the "
            "allowlist file with a reason. The matched text is deliberately not printed here."
        )
        return 1

    print(f"No unallowlisted findings ({len(findings)} reported, {sum(suppressed.values())} retired).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
