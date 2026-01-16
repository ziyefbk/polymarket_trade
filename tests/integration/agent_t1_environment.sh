#!/bin/bash
# Agent T1: Environment Verification
# Priority: 🔥 Critical - Must pass before any other tests

set -e  # Exit immediately if any command fails

OUTPUT_DIR="test_reports"
REPORT_FILE="$OUTPUT_DIR/t1_environment_report.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Agent T1: Environment Verification"
echo "=============================================="
echo ""

mkdir -p "$OUTPUT_DIR"

# Start report
echo "=== Environment Verification Report ===" > "$REPORT_FILE"
echo "Date: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

TESTS_PASSED=0
TESTS_FAILED=0

# Function to check and report
check_requirement() {
    local test_name="$1"
    local command="$2"
    local expected="$3"

    echo -n "Checking $test_name... "

    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "[PASS] $test_name" >> "$REPORT_FILE"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "[FAIL] $test_name: $expected" >> "$REPORT_FILE"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Python Version Check
echo "1️⃣ Python Environment"
echo "" >> "$REPORT_FILE"
echo "--- Python Environment ---" >> "$REPORT_FILE"

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION" | tee -a "$REPORT_FILE"

if python -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
    echo -e "${GREEN}✓ Python 3.7+ detected${NC}"
    echo "[PASS] Python version >= 3.7" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Python 3.7+ required (found $PYTHON_VERSION)${NC}"
    echo "[FAIL] Python version check: Found $PYTHON_VERSION, requires >= 3.7" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
fi

echo "" >> "$REPORT_FILE"

# 2. Dependencies Check
echo ""
echo "2️⃣ Python Dependencies"
echo "--- Python Dependencies ---" >> "$REPORT_FILE"

REQUIRED_PACKAGES=(
    "httpx"
    "sqlalchemy"
    "aiosqlite"
    "loguru"
    "apscheduler"
    "fastapi"
    "uvicorn"
    "pytest"
    "pytest-asyncio"
    "alembic"
    "py_clob_client"
    "eth_account"
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    check_requirement "$package" "python -c 'import ${package//-/_}'" "Package $package not installed"
done

echo "" >> "$REPORT_FILE"

# 3. Environment Variables
echo ""
echo "3️⃣ Environment Variables"
echo "--- Environment Variables ---" >> "$REPORT_FILE"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    echo "[PASS] .env file found" >> "$REPORT_FILE"
    ((TESTS_PASSED++))

    # Check required variables (without printing values)
    check_requirement "POLYMARKET_PRIVATE_KEY" "grep -q POLYMARKET_PRIVATE_KEY .env" ".env missing POLYMARKET_PRIVATE_KEY"
    check_requirement "DATABASE_URL" "grep -q DATABASE_URL .env" ".env missing DATABASE_URL"
else
    echo -e "${RED}✗ .env file not found${NC}"
    echo "[FAIL] .env file missing" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
fi

echo "" >> "$REPORT_FILE"

# 4. File Structure
echo ""
echo "4️⃣ Project Structure"
echo "--- Project Structure ---" >> "$REPORT_FILE"

REQUIRED_FILES=(
    "config/settings.py"
    "src/api/polymarket_client.py"
    "src/api/trader.py"
    "src/analyzer/arbitrage_detector.py"
    "src/strategy/arbitrage_executor.py"
    "src/strategy/position_manager.py"
    "src/utils/database.py"
    "src/utils/kelly.py"
    "src/utils/logger.py"
    "src/utils/models.py"
    "main.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    check_requirement "$file" "test -f $file" "File $file not found"
done

echo "" >> "$REPORT_FILE"

# 5. Database Check
echo ""
echo "5️⃣ Database Connectivity"
echo "--- Database Connectivity ---" >> "$REPORT_FILE"

if python -c "from src.utils.database import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().initialize())" 2>/dev/null; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
    echo "[PASS] Database initialization" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ Database connection failed (may be expected if not initialized)${NC}"
    echo "[WARN] Database initialization failed" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# Summary
echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

echo "--- Summary ---" >> "$REPORT_FILE"
echo "Tests Passed: $TESTS_PASSED" >> "$REPORT_FILE"
echo "Tests Failed: $TESTS_FAILED" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All environment checks passed!${NC}"
    echo "[RESULT] SUCCESS - Environment is ready for integration testing" >> "$REPORT_FILE"
    exit 0
else
    echo -e "${RED}✗ $TESTS_FAILED checks failed. Please fix before proceeding.${NC}"
    echo "[RESULT] FAILURE - Environment has $TESTS_FAILED issue(s)" >> "$REPORT_FILE"
    exit 1
fi