#!/bin/bash

# Run all web client tests

set -e

echo "=========================================="
echo "Web Client Test Suite"
echo "=========================================="
echo ""

# Track results
TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_TESTS=""

# Test 1: Code structure and validation
echo "Running: Code Structure Tests..."
if node tests/test_web_client.js; then
    echo "✓ Code structure tests passed"
    echo ""
else
    echo "✗ Code structure tests failed"
    FAILED_TESTS="$FAILED_TESTS\n  - Code structure tests"
    echo ""
fi

# Test 2: DAG algorithm
echo "Running: DAG Algorithm Tests..."
if node tests/test_dag_algorithm.js; then
    echo "✓ DAG algorithm tests passed"
    echo ""
else
    echo "✗ DAG algorithm tests failed"
    FAILED_TESTS="$FAILED_TESTS\n  - DAG algorithm tests"
    echo ""
fi

# Test 3: API integration
echo "Running: API Integration Tests..."
if node tests/test_api_integration.js; then
    echo "✓ API integration tests passed"
    echo ""
else
    echo "✗ API integration tests failed"
    FAILED_TESTS="$FAILED_TESTS\n  - API integration tests"
    echo ""
fi

echo "=========================================="
echo "Web Client Test Summary"
echo "=========================================="
echo ""

if [ -z "$FAILED_TESTS" ]; then
    echo "✅ ALL WEB CLIENT TESTS PASSED!"
    echo ""
    echo "Test Coverage:"
    echo "  • Code structure and validation (25 tests)"
    echo "  • DAG layout algorithm (7 tests)"
    echo "  • API integration patterns (25 tests)"
    echo ""
    echo "Total: 57 tests passed"
    echo "=========================================="
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    echo ""
    echo "Failed test suites:$FAILED_TESTS"
    echo ""
    echo "=========================================="
    exit 1
fi
