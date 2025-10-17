# Testing Guide

This document explains how the secrets-scanner GitHub Action testing works.

## Test Structure

The integration tests use a **matrix strategy** in `.github/workflows/integration-tests.yml` that runs multiple test scenarios in parallel. Each test validates different aspects of the action's behavior.

### Key Test Categories

1. **Input Validation** - Tests parameter validation and error handling
2. **Built-in Rules** - Verifies Gitleaks built-in secret detection works
3. **Custom Rules** - Tests HMCTS-specific regex patterns when enabled
4. **Leak Counting** - Validates exact number of secrets detected

### Test Data

The `test_scans/` directory contains two types of test files:

**Existing Files** (for manual testing):
- `application.yaml`, `docker-compose.*.yml`, `examples.txt` - Real-world configuration examples for manual testing

**Integration Test Files** (for automated testing):
- `test_internal_urls.txt` - URLs matching custom regex patterns
- `test_system_ids.txt` - System IDs matching custom regex patterns  
- `test_builtin_secrets.txt` - Secrets detected by built-in rules
- `test_clean_code.txt` - Clean code with no secrets

## Running Tests

### Automated
Tests run automatically on pull requests and can be triggered manually via GitHub Actions.

### Local Testing
```bash
# Test with custom rules
gitleaks detect --source test_scans/ --config gitleaks-hmcts-rules-template.toml

# Test with built-in rules only
gitleaks detect --source test_scans/
```

## Understanding Test Results

Tests validate:
- **Exit codes** - Success (0) vs failure (1) based on whether secrets are found
- **Leak counts** - Exact number of custom vs built-in rule matches (using tag-based classification)
- **Rule separation** - Custom rules only run when `run_hmcts_rules=true`

## Pipeline Results Display

### Successful Pipeline
When all tests pass, you'll see:
```
✅ Test PASSED: Action completed successfully as expected
✅ Test PASSED: Action failed as expected  
✅ CUSTOM RULE LEAKS VALIDATION PASSED: Found expected 4 custom leaks
✅ BUILT-IN RULE LEAKS VALIDATION PASSED: Found expected 1 built-in leaks
```

### Failed Pipeline
When tests fail, you'll see:
```
❌ Test FAILED: Unexpected result
Expected exit code: X
Actual outcome: Y
❌ CUSTOM RULE LEAKS VALIDATION FAILED: Expected 4 custom leaks, found 2
❌ BUILT-IN RULE LEAKS VALIDATION FAILED: Expected 1 built-in leaks, found 0
```

### Detailed Output
Each test case shows:
- Test case name and description
- Expected vs actual exit codes
- Expected behavior vs actual outcome
- Leak breakdown by rule type (custom vs built-in)
- Specific file locations and matches found

## References

- [Gitleaks Documentation](https://gitleaks.io/)
- [GitHub Actions Matrix Strategy](https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs)
- [TruffleHog Documentation](https://trufflesecurity.com/trufflehog/)
