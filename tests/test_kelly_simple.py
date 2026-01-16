"""
Simple test runner to verify Kelly and PositionManager functionality
Run this directly without pytest to avoid import issues
"""
import sys
sys.path.insert(0, '..')

# Import directly from the module files
import importlib.util

def load_module_from_file(module_name, file_path):
    """Load a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load kelly module
kelly = load_module_from_file("kelly", "../src/utils/kelly.py")

print("=" * 60)
print("Testing Kelly Criterion Functions")
print("=" * 60)

# Test 1: Basic Kelly calculation
print("\nTest 1: Basic Kelly Calculation")
try:
    result = kelly.calculate_kelly_fraction(0.99, 0.02, conservative_factor=0.5)
    print(f"✓ calculate_kelly_fraction(0.99, 0.02, 0.5) = {result:.4f}")
    assert 0 < result <= 0.25, f"Expected 0 < result <= 0.25, got {result}"
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 2: Perfect arbitrage
print("\nTest 2: Perfect Arbitrage (100% win probability)")
try:
    result = kelly.calculate_kelly_fraction(1.0, 0.05, conservative_factor=1.0)
    print(f"✓ calculate_kelly_fraction(1.0, 0.05, 1.0) = {result:.4f}")
    assert result == 0.25, f"Expected 0.25, got {result}"
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 3: Zero win probability
print("\nTest 3: Zero Win Probability")
try:
    result = kelly.calculate_kelly_fraction(0.0, 0.05)
    print(f"✓ calculate_kelly_fraction(0.0, 0.05) = {result:.4f}")
    assert result == 0.0, f"Expected 0.0, got {result}"
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 4: Calculate position size
print("\nTest 4: Calculate Position Size")
try:
    result = kelly.calculate_position_size(10000.0, 0.95, 0.05, max_position_size=1000.0)
    print(f"✓ calculate_position_size(10000, 0.95, 0.05, max=1000) = ${result:.2f}")
    assert 0 <= result <= 1000.0, f"Expected 0 <= result <= 1000, got {result}"
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 5: Estimate execution probability
print("\nTest 5: Estimate Execution Probability")
try:
    result = kelly.estimate_execution_probability(100000.0, 1000.0, 0.9, 0.01)
    print(f"✓ estimate_execution_probability(100k, 1k, 0.9, 0.01) = {result:.4f}")
    assert 0 <= result <= 1.0, f"Expected 0 <= result <= 1, got {result}"
    assert result > 0.5, f"Expected high probability, got {result}"
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 6: Low liquidity reduces probability
print("\nTest 6: Low Liquidity Reduces Probability")
try:
    high_liq = kelly.estimate_execution_probability(100000.0, 1000.0, 0.9, 0.01)
    low_liq = kelly.estimate_execution_probability(5000.0, 2000.0, 0.9, 0.01)
    print(f"✓ High liquidity: {high_liq:.4f}, Low liquidity: {low_liq:.4f}")
    assert high_liq > low_liq, f"Expected high_liq > low_liq, got {high_liq} <= {low_liq}"
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 7: Invalid inputs
print("\nTest 7: Invalid Input Handling")
try:
    kelly.calculate_kelly_fraction(1.5, 0.05)  # Invalid win probability
    print("✗ Should have raised ValueError for invalid win_probability")
except ValueError as e:
    print(f"✓ Correctly raised ValueError: {str(e)[:50]}...")

try:
    kelly.calculate_kelly_fraction(0.9, -0.05)  # Invalid profit ratio
    print("✗ Should have raised ValueError for negative profit_ratio")
except ValueError as e:
    print(f"✓ Correctly raised ValueError: {str(e)[:50]}...")

print("\n" + "=" * 60)
print("All Kelly Criterion tests completed!")
print("=" * 60)

# Integration test
print("\n" + "=" * 60)
print("Integration Test: Realistic Arbitrage Scenario")
print("=" * 60)

print("\nScenario: $10k capital, good liquidity, 3% profit opportunity")
liquidity = 100000.0
required_size = 1000.0
confidence = 0.9
available_capital = 10000.0
profit_ratio = 0.03

# Step 1: Estimate execution probability
exec_prob = kelly.estimate_execution_probability(liquidity, required_size, confidence, 0.01)
print(f"Step 1: Execution probability = {exec_prob:.2%}")

# Step 2: Calculate position size
position_size = kelly.calculate_position_size(
    available_capital,
    exec_prob,
    profit_ratio,
    max_position_size=1000.0,
    conservative_factor=0.5
)
print(f"Step 2: Optimal position size = ${position_size:.2f}")

# Step 3: Calculate expected profit
expected_profit = position_size * profit_ratio
print(f"Step 3: Expected profit = ${expected_profit:.2f}")

print("\n✓ Integration test completed successfully!")
