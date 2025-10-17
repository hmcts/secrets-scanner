# Testing Guide

This is a concise guide to how integration tests are structured and what to expect.

## Structure and Execution

- **Sequential jobs**: Tests run one after another via `needs:` in `.github/workflows/integration-tests.yml` to avoid conflicts.
- **Shared helpers**: Common logic lives in `.github/scripts/test-helpers.sh` (workspace prep, counting leaks, validation).
- **Test workspace**: Each test starts from a clean `test_workspace/` directory created by helpers to ensure isolation.

## How tests run (high level)

1. Prepare workspace:
   - For data-driven tests, helper copies fixtures from `test_scans/` into `test_workspace/` and initializes a minimal git repo.
   - For “no leaks” tests, helper creates an empty clean repo.
2. Execute the action with `test_mode: "true"`:
   - In test mode the action runs Gitleaks in Docker against `test_workspace/` and writes `gitleaks-report.json` there.
   - Built-in vs custom rules are controlled by `run_hmcts_rules` and required regex inputs.
3. Validate results:
   - Helpers parse the report with `jq` and validate counts of custom vs built-in leaks using tag `hmcts-custom-scan`.

## Fixtures

- `test_scans/test_internal_urls.txt`: data to trigger custom internal URL rule(s).
- `test_scans/test_system_ids.txt`: data to trigger custom system ID rule(s).
- `test_scans/test_builtin_secrets.txt`: data to trigger built-in rules.

## Results and Annotations

- Step logs show a chained summary per job (name, description, expected behavior, and leak counts).
- If the action emits annotations (e.g., input validation uses `::error` in production behavior), they will appear in the run. In tests we rely on leak counts and summaries to judge pass/fail; annotations are expected when validation fails.

## Inputs relevant to tests

- `run_hmcts_rules` (boolean): Enables HMCTS custom rules.
- `hmcts_regex_internal_urls` (string): Required when `run_hmcts_rules=true`.
- `hmcts_regex_system_ids` (string): Required when `run_hmcts_rules=true`.
- `test_mode` (string "true"|"false"): Internal test switch to run Gitleaks via Docker against `test_workspace/` and avoid scanning repo history. Defaults to "false".

## References

- Gitleaks: https://gitleaks.io/
- GitHub Actions jobs and workflows: https://docs.github.com/en/actions
