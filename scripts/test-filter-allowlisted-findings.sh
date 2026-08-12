#!/usr/bin/env bash
# Behaviour tests for filter-allowlisted-findings.py.
#
# The exit codes carry the meaning, so they are what is asserted: 0 lets a build
# through, 1 fails it on a finding, and 2 refuses on an allowlist that cannot be
# trusted. Getting 2 wrong is the dangerous one - a malformed allowlist that
# exited 0 would read as "nothing to report".
#
# No network, no docker: the input is a fixture in TruffleHog's JSON-lines shape.
# Run: scripts/test-filter-allowlisted-findings.sh
set -uo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
filter="$here/filter-allowlisted-findings.py"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Two findings sharing one detector and matched text - one in a file, one in a
# commit message (no `file` key at all, which is the case path scoping cannot
# reach) - plus a second, different finding.
cat > "$work/findings.json" <<'JSON'
{"SourceMetadata":{"Data":{"Git":{"commit":"1111111111111111111111111111111111111111","file":"tests/test_thing.py","line":12}}},"DetectorName":"Lob","Raw":"test_a_name_long_enough_to_look_like_a_key","Verified":true}
{"SourceMetadata":{"Data":{"Git":{"commit":"2222222222222222222222222222222222222222","line":3}}},"DetectorName":"Lob","Raw":"test_a_name_long_enough_to_look_like_a_key","Verified":true}
{"SourceMetadata":{"Data":{"Git":{"commit":"3333333333333333333333333333333333333333","file":"src/app.py","line":7}}},"DetectorName":"Stripe","Raw":"sk_live_pretend_value_for_the_test","Verified":true}
JSON

fp() { python3 -c "import hashlib,sys;print(hashlib.sha256((sys.argv[1]+chr(10)+sys.argv[2]).encode()).hexdigest())" "$1" "$2"; }
LOB=$(fp Lob test_a_name_long_enough_to_look_like_a_key)
STRIPE=$(fp Stripe sk_live_pretend_value_for_the_test)

pass=0 fail=0
check() { # check <name> <expected-exit> <allowlist-file>
  out=$(python3 "$filter" --allowlist "$3" < "$work/findings.json" 2>&1); code=$?
  if [ "$code" = "$2" ]; then pass=$((pass+1)); printf '  ok    %-58s exit %s\n' "$1" "$code"
  else fail=$((fail+1)); printf '  FAIL  %-58s exit %s, wanted %s\n%s\n' "$1" "$code" "$2" "$out"; fi
  printf '%s' "$out" > "$work/last.out"
}

echo "one fingerprint covers both a file and a commit-message occurrence"
printf '%s  known false positive\n' "$LOB" > "$work/lob-only"
check "unrelated finding still fails the build" 1 "$work/lob-only"
grep -q 'Stripe' "$work/last.out" || { echo "  FAIL  the surviving finding was not named"; fail=$((fail+1)); }
grep -q 'sk_live_pretend_value_for_the_test' "$work/last.out" && { echo "  FAIL  matched text leaked into output"; fail=$((fail+1)); } || pass=$((pass+1))

printf '%s  known false positive\n%s  accepted for this test\n' "$LOB" "$STRIPE" > "$work/both"
check "every finding allowlisted, build passes" 0 "$work/both"

echo "an allowlist that cannot be trusted must refuse, never pass"
printf 'nonsense  a reason\n' > "$work/bad-fp"
check "fingerprint that is not 64 hex characters" 2 "$work/bad-fp"
printf '%s\n' "$LOB" > "$work/no-reason"
check "entry with no reason" 2 "$work/no-reason"
printf '%s  one\n%s  two\n' "$LOB" "$LOB" > "$work/dupe"
check "same fingerprint listed twice" 2 "$work/dupe"
check "allowlist file that does not exist" 2 "$work/absent"

echo "a stale entry is reported, but does not fail the build"
printf '%s  known false positive\n%s  accepted for this test\n%s  long gone\n' \
  "$LOB" "$STRIPE" "$(fp Stripe sk_live_no_longer_present)" > "$work/stale"
check "stale entry warns only" 0 "$work/stale"
grep -q 'matched nothing' "$work/last.out" && pass=$((pass+1)) || { echo "  FAIL  stale entry not reported"; fail=$((fail+1)); }

printf '\n%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
