#!/bin/bash
# Agent T2: Unit Tests Execution
# Priority: 🔥 High - Must pass before integration tests

set -e  # Exit immediately if any command fails

OUTPUT_DIR="test_reports"
REPORT_FILE="$OUTPUT_DIR/t2_unit_tests_report.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Agent T2: Unit Tests Execution"
echo "=============================================="
echo ""

mkdir -p "$OUTPUT_DIR"

# Start report
echo "=== Unit Tests Execution Report ===" > "$REPORT_FILE"
echo "Date: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test and capture results
run_test_suite() {
    local test_file="$1"
    local test_name="$2"

    echo ""
    echo "Running: $test_name"
    echo "--- $test_name ---" >> "$REPORT_FILE"

    if pytest "$test_file" -v --tb=short 2>&1 | tee -a "$REPORT_FILE"; then
        echo -e "${GREEN}✓ $test_name PASSED${NC}"
        echo "[PASS] $test_name" >> "$REPORT_FILE"
        return 0
    else
        echo -e "${RED}✗ $test_name FAILED${NC}"
        echo "[FAIL] $test_name" >> "$REPORT_FILE"
        return 1
    fi
}

# 1. Kelly Criterion Tests
echo "1️⃣ Testing Kelly Criterion Utilities"
if run_test_suite "tests/test_kelly.py" "Kelly Criterion Tests"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

# 2. Position Manager Tests
echo ""
echo "2️⃣ Testing Position Manager"
if run_test_suite "tests/test_position_manager.py" "Position Manager Tests"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

# 3. Arbitrage Detector Tests
echo ""
echo "3️⃣ Testing Arbitrage Detector"
if run_test_suite "tests/test_arbitrage_detector.py" "Arbitrage Detector Tests"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

# 4. Database Layer Tests
echo ""
echo "4️⃣ Testing Database Layer"
if run_test_suite "tests/test_database.py" "Database Tests"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

# 5. Orchestrator Tests
echo ""
echo "5️⃣ Testing Main Orchestrator"
if run_test_suite "tests/test_orchestrator.py" "Orchestrator Tests"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

# Summary
echo ""
echo "=============================================="
echo "Unit Tests Summary"
echo "=============================================="
echo "Total Test Suites: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

echo "" >> "$REPORT_FILE"
echo "--- Summary ---" >> "$REPORT_FILE"
echo "Total Test Suites: $TOTAL_TESTS" >> "$REPORT_FILE"
echo "Passed: $PASSED_TESTS" >> "$REPORT_FILE"
echo "Failed: $FAILED_TESTS" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All unit tests passed!${NC}"
    echo "[RESULT] SUCCESS - All unit tests passed" >> "$REPORT_FILE"
    exit 0
else
    echo -e "${RED}✗ $FAILED_TESTS test suite(s) failed${NC}"
    echo "[RESULT] FAILURE - $FAILED_TESTS test suite(s) failed" >> "$REPORT_FILE"
    exit 1
fi