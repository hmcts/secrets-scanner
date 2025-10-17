#!/bin/bash

# Common test helper functions for integration tests

# Function to prepare test workspace
prepare_test_workspace() {
  # Create a clean test directory to avoid scanning commit history
  mkdir -p test_workspace
  cd test_workspace
  
  # Copy only the specific test files we need
  cp ../test_scans/test_internal_urls.txt .
  cp ../test_scans/test_system_ids.txt .
  cp ../test_scans/test_builtin_secrets.txt .
  
  # Copy action files to test workspace
  cp ../action.yml .
  cp ../gitleaks-hmcts-rules-template.toml .
  
  # Initialize git in test workspace to avoid scanning parent repo history
  git init
  git config user.email "test@example.com"
  git config user.name "Test User"
  git add .
  git commit -m "Test commit"
  
  # Change back to parent directory
  cd ..
}

# Function to count leaks from Gitleaks report
count_leaks_from_report() {
  # Report should be in test_workspace directory
  if [ -f "test_workspace/gitleaks-report.json" ]; then
    # Calculate leak counts
    CUSTOM_LEAKS=$(jq '[.[] | select(.tags[] | contains("hmcts-custom-scan"))] | length' test_workspace/gitleaks-report.json)
    BUILTIN_LEAKS=$(jq '[.[] | select(.tags[] | contains("hmcts-custom-scan") | not)] | length' test_workspace/gitleaks-report.json)
    
    # Add to GitHub output
    echo "custom_leaks=$CUSTOM_LEAKS" >> $GITHUB_OUTPUT
    echo "builtin_leaks=$BUILTIN_LEAKS" >> $GITHUB_OUTPUT
    
    # Print summary
    echo "Leak counts - Custom: $CUSTOM_LEAKS, Built-in: $BUILTIN_LEAKS"
    
    # Print full JSON for debugging
    echo "=== GITLEAKS REPORT JSON (for debugging) ==="
    cat test_workspace/gitleaks-report.json
  else
    echo "custom_leaks=0" >> $GITHUB_OUTPUT
    echo "builtin_leaks=0" >> $GITHUB_OUTPUT
    echo "No Gitleaks report found"
  fi
}

# Function to validate leak counts
validate_leak_counts() {
  local expected_custom=$1
  local expected_builtin=$2
  
  echo ""
  echo "=== LEAK TYPE VALIDATION ==="
  echo "Expected Custom Rule Leaks: $expected_custom"
  echo "Actual Custom Rule Leaks: ${{ steps.count_leaks.outputs.custom_leaks }}"
  echo "Expected Built-in Rule Leaks: $expected_builtin"            
  echo "Actual Built-in Rule Leaks: ${{ steps.count_leaks.outputs.builtin_leaks }}"
  
  # Validate custom rule leaks
  if [ "${{ steps.count_leaks.outputs.custom_leaks }}" = "$expected_custom" ]; then
    echo "✅ CUSTOM RULE LEAKS VALIDATION PASSED: Found expected $expected_custom custom leaks"
  else
    echo "❌ CUSTOM RULE LEAKS VALIDATION FAILED: Expected $expected_custom custom leaks, found ${{ steps.count_leaks.outputs.custom_leaks }}"
    exit 1
  fi
  
  # Validate built-in rule leaks
  if [ "${{ steps.count_leaks.outputs.builtin_leaks }}" = "$expected_builtin" ]; then
    echo "✅ BUILT-IN RULE LEAKS VALIDATION PASSED: Found expected $expected_builtin built-in leaks"
  else
    echo "❌ BUILT-IN RULE LEAKS VALIDATION FAILED: Expected $expected_builtin built-in leaks, found ${{ steps.count_leaks.outputs.builtin_leaks }}"
    exit 1
  fi
}
