#!/bin/bash

# Common test helper functions for integration tests

# Function to prepare test workspace
prepare_test_workspace() {
  # Create a clean test directory to avoid scanning commit history
  rm -rf test_workspace
  mkdir -p test_workspace
  cd test_workspace
  
  # Copy only the specific test files we need
  cp ../test_scans/test_internal_urls.txt .
  cp ../test_scans/test_system_ids.txt .
  cp ../test_scans/test_builtin_secrets.txt .
  
  # Initialize git in test workspace to avoid scanning parent repo history
  git init
  git config user.email "test@example.com"
  git config user.name "Test User"
  git add .
  git commit -m "Test commit"
  
  # Change back to parent directory so gitleaks runs in test_workspace
  cd ..
}

# Function to prepare an empty test workspace (no leaks expected)
prepare_empty_test_workspace() {
  rm -rf test_workspace
  mkdir -p test_workspace
  cd test_workspace
  git init
  git config user.email "test@example.com"
  git config user.name "Test User"
  echo "clean" > test_clean_code.txt
  git add .
  git commit -m "Clean workspace"
  cd ..
}

# Function to count leaks from Gitleaks report
count_leaks_from_report() {
  # Report path produced by Docker in test mode
  REPORT_PATH="test_workspace/gitleaks-report.json"
  if [ -f "$REPORT_PATH" ]; then
    # Calculate leak counts (tolerate findings with missing/null tags)
    # Report schema uses capitalized keys (Tags). Fall back to lower-case if needed.
    CUSTOM_LEAKS=$(jq '[.[] | select(((.Tags // .tags // []) | index("hmcts-custom-scan"))) ] | length' "$REPORT_PATH")
    BUILTIN_LEAKS=$(jq '[.[] | select(((((.Tags // .tags // []) | index("hmcts-custom-scan"))) | not)) ] | length' "$REPORT_PATH")
    
    # Add to GitHub output and environment for downstream steps
    echo "custom_leaks=$CUSTOM_LEAKS" >> $GITHUB_OUTPUT
    echo "builtin_leaks=$BUILTIN_LEAKS" >> $GITHUB_OUTPUT
    echo "CUSTOM_LEAKS=$CUSTOM_LEAKS" >> $GITHUB_ENV
    echo "BUILTIN_LEAKS=$BUILTIN_LEAKS" >> $GITHUB_ENV
    
    # Print summary
    echo "Leak counts - Custom: $CUSTOM_LEAKS, Built-in: $BUILTIN_LEAKS"
    
    # Print full JSON for debugging
    echo "=== GITLEAKS REPORT JSON (for debugging) ==="
    cat "$REPORT_PATH"
  else
    echo "No Gitleaks report found"
    echo "custom_leaks=0" >> $GITHUB_OUTPUT
    echo "builtin_leaks=0" >> $GITHUB_OUTPUT
    echo "CUSTOM_LEAKS=0" >> $GITHUB_ENV
    echo "BUILTIN_LEAKS=0" >> $GITHUB_ENV
  fi
}

# Function to validate leak counts
validate_leak_counts() {
  local expected_custom=$1
  local expected_builtin=$2
  
  echo ""
  echo "=== LEAK TYPE VALIDATION ==="
  echo "Expected Custom Rule Leaks: $expected_custom"
  echo "Actual Custom Rule Leaks: ${CUSTOM_LEAKS:-unset}"
  echo "Expected Built-in Rule Leaks: $expected_builtin"            
  echo "Actual Built-in Rule Leaks: ${BUILTIN_LEAKS:-unset}"
  
  # Validate custom rule leaks
  if [ "${CUSTOM_LEAKS:-}" = "$expected_custom" ]; then
    echo "✅ CUSTOM RULE LEAKS VALIDATION PASSED: Found expected $expected_custom custom leaks"
  else
    echo "❌ CUSTOM RULE LEAKS VALIDATION FAILED: Expected $expected_custom custom leaks, found ${CUSTOM_LEAKS:-unset}"
    exit 1
  fi
  
  # Validate built-in rule leaks
  if [ "${BUILTIN_LEAKS:-}" = "$expected_builtin" ]; then
    echo "✅ BUILT-IN RULE LEAKS VALIDATION PASSED: Found expected $expected_builtin built-in leaks"
  else
    echo "❌ BUILT-IN RULE LEAKS VALIDATION FAILED: Expected $expected_builtin built-in leaks, found ${BUILTIN_LEAKS:-unset}"
    exit 1
  fi
}
