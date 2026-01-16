"""
Standalone test for Kelly Criterion - tests the logic directly
"""

def calculate_kelly_fraction(
    win_probability: float,
    profit_ratio: float,
    max_fraction: float = 0.25,
    conservative_factor: float = 0.5
) -> float:
    """Calculate optimal position size using Kelly Criterion"""
    # Validate inputs
    if not 0 <= win_probability <= 1:
        raise ValueError(f"Win probability must be between 0 and 1, got {win_probability}")
    if profit_ratio <= 0:
        raise ValueError(f"Profit ratio must be positive, got {profit_ratio}")
    if not 0 < max_fraction <= 1:
        raise ValueError(f"Max fraction must be between 0 and 1, got {max_fraction}")
    if not 0 < conservative_factor <= 1:
        raise ValueError(f"Conservative factor must be between 0 and 1, got {conservative_factor}")

    if win_probability == 0:
        return 0.0

    if win_probability == 1:
        kelly_fraction = max_fraction
    else:
        loss_probability = 1 - win_probability
        kelly_fraction = (profit_ratio * win_probability - loss_probability) / profit_ratio

        if kelly_fraction < 0:
            return 0.0

    adjusted_fraction = kelly_fraction * conservative_factor
    final_fraction = min(adjusted_fraction, max_fraction)

    return final_fraction


def calculate_position_size(
    available_capital: float,
    win_probability: float,
    profit_ratio: float,
    max_position_size: float = None,
    conservative_factor: float = 0.5
) -> float:
    """Calculate optimal position size in USD"""
    if available_capital <= 0:
        raise ValueError(f"Available capital must be positive, got {available_capital}")

    kelly_fraction = calculate_kelly_fraction(
        win_probability=win_probability,
        profit_ratio=profit_ratio,
        max_fraction=0.25,
        conservative_factor=conservative_factor
    )

    position_size = available_capital * kelly_fraction

    if max_position_size is not None:
        position_size = min(position_size, max_position_size)

    return position_size


def estimate_execution_probability(
    liquidity: float,
    required_size: float,
    confidence_score: float,
    slippage_tolerance: float = 0.01
) -> float:
    """Estimate probability of successful execution"""
    if liquidity <= 0 or required_size <= 0:
        return 0.0

    liquidity_ratio = required_size / liquidity

    if liquidity_ratio > 0.5:
        liquidity_factor = 0.3
    elif liquidity_ratio > 0.3:
        liquidity_factor = 0.6
    elif liquidity_ratio > 0.1:
        liquidity_factor = 0.8
    else:
        liquidity_factor = 0.95

    confidence_factor = confidence_score
    slippage_factor = 1 - (slippage_tolerance * 2)
    slippage_factor = max(0.7, min(slippage_factor, 1.0))

    execution_probability = (
        liquidity_factor ** 0.4 *
        confidence_factor ** 0.4 *
        slippage_factor ** 0.2
    )

    return execution_probability


# Run tests
print("=" * 70)
print("KELLY CRITERION TESTS")
print("=" * 70)

tests_passed = 0
tests_failed = 0

def run_test(name, test_func):
    global tests_passed, tests_failed
    try:
        test_func()
        print(f"[PASS] {name}")
        tests_passed += 1
    except AssertionError as e:
        print(f"[FAIL] {name}: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {e}")
        tests_failed += 1

# Test Suite
def test_basic_kelly():
    result = calculate_kelly_fraction(0.99, 0.02, conservative_factor=0.5)
    assert 0 < result <= 0.25, f"Expected 0 < result <= 0.25, got {result}"

def test_perfect_arbitrage():
    result = calculate_kelly_fraction(1.0, 0.05, conservative_factor=1.0)
    assert result == 0.25, f"Expected 0.25, got {result}"

def test_zero_win_probability():
    result = calculate_kelly_fraction(0.0, 0.05)
    assert result == 0.0, f"Expected 0.0, got {result}"

def test_negative_kelly():
    result = calculate_kelly_fraction(0.50, 0.01, conservative_factor=1.0)
    assert result == 0.0, f"Expected 0.0 for negative Kelly, got {result}"

def test_conservative_factor():
    full = calculate_kelly_fraction(0.99, 0.05, conservative_factor=1.0)
    half = calculate_kelly_fraction(0.99, 0.05, conservative_factor=0.5)
    assert half < full, f"Half Kelly should be less than full Kelly"

def test_position_size_basic():
    result = calculate_position_size(10000.0, 0.95, 0.05, max_position_size=1000.0)
    assert 0 <= result <= 1000.0, f"Expected 0 <= result <= 1000, got {result}"

def test_position_size_max_cap():
    result = calculate_position_size(100000.0, 0.99, 0.10, max_position_size=500.0)
    assert result <= 500.0, f"Expected result <= 500, got {result}"

def test_execution_probability_high_liquidity():
    result = estimate_execution_probability(100000.0, 1000.0, 0.9, 0.01)
    assert 0 <= result <= 1.0, f"Probability must be 0-1, got {result}"
    assert result > 0.5, f"Expected high probability, got {result}"

def test_execution_probability_low_liquidity():
    result = estimate_execution_probability(5000.0, 2000.0, 0.9, 0.01)
    assert 0 <= result <= 1.0, f"Probability must be 0-1, got {result}"
    assert result < 0.8, f"Expected lower probability, got {result}"

def test_execution_probability_comparison():
    high = estimate_execution_probability(100000.0, 1000.0, 0.9, 0.01)
    low = estimate_execution_probability(5000.0, 2000.0, 0.9, 0.01)
    assert high > low, f"High liquidity should have higher probability"

def test_invalid_win_probability():
    try:
        calculate_kelly_fraction(1.5, 0.05)
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_invalid_profit_ratio():
    try:
        calculate_kelly_fraction(0.9, -0.05)
        assert False, "Should raise ValueError"
    except ValueError:
        pass

# Run all tests
print("\n1. Basic Tests:")
run_test("Basic Kelly calculation", test_basic_kelly)
run_test("Perfect arbitrage (100% win)", test_perfect_arbitrage)
run_test("Zero win probability", test_zero_win_probability)
run_test("Negative Kelly returns zero", test_negative_kelly)
run_test("Conservative factor reduces size", test_conservative_factor)

print("\n2. Position Size Tests:")
run_test("Basic position size", test_position_size_basic)
run_test("Position size respects max cap", test_position_size_max_cap)

print("\n3. Execution Probability Tests:")
run_test("High liquidity probability", test_execution_probability_high_liquidity)
run_test("Low liquidity probability", test_execution_probability_low_liquidity)
run_test("Liquidity comparison", test_execution_probability_comparison)

print("\n4. Input Validation Tests:")
run_test("Invalid win probability raises error", test_invalid_win_probability)
run_test("Invalid profit ratio raises error", test_invalid_profit_ratio)

print("\n" + "=" * 70)
print("INTEGRATION TEST: Realistic Arbitrage Scenario")
print("=" * 70)

print("\nScenario: $10k capital, good liquidity, 3% profit opportunity")
liquidity = 100000.0
required_size = 1000.0
confidence = 0.9
available_capital = 10000.0
profit_ratio = 0.03

exec_prob = estimate_execution_probability(liquidity, required_size, confidence, 0.01)
print(f"  Execution probability: {exec_prob:.2%}")

position_size = calculate_position_size(
    available_capital, exec_prob, profit_ratio, max_position_size=1000.0, conservative_factor=0.5
)
print(f"  Optimal position size: ${position_size:.2f}")

expected_profit = position_size * profit_ratio
print(f"  Expected profit: ${expected_profit:.2f}")

assert 100 <= position_size <= 1000, f"Position size out of reasonable range: ${position_size:.2f}"
print("  [PASS] Integration test passed!")

print("\n" + "=" * 70)
print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
print("=" * 70)

if tests_failed == 0:
    print("\nAll tests passed successfully!")
else:
    print(f"\n{tests_failed} test(s) failed")
    exit(1)