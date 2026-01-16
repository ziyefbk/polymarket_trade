"""
Simple validation script for arbitrage detector without external dependencies

This script validates the core logic without requiring all dependencies installed.
"""
import sys
sys.path.insert(0, '.')

# Mock the dependencies
class MockSettings:
    class Arbitrage:
        min_discrepancy = 0.03

    class Trading:
        max_position_size = 1000.0
        min_profit_threshold = 0.02
        slippage_tolerance = 0.01

    arbitrage = Arbitrage()
    trading = Trading()

sys.modules['config'] = type(sys)('config')
sys.modules['config'].settings = MockSettings()

# Now we can import after mocking
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.api.polymarket_client import Event, Market

def create_test_event(yes_price, no_price, yes_liquidity=50000.0, no_liquidity=50000.0):
    """Create a test event"""
    yes_market = Market(
        token_id="token_yes",
        condition_id="cond_1",
        question="Test question",
        outcome="YES",
        price=yes_price,
        volume=10000.0,
        liquidity=yes_liquidity
    )

    no_market = Market(
        token_id="token_no",
        condition_id="cond_1",
        question="Test question",
        outcome="NO",
        price=no_price,
        volume=10000.0,
        liquidity=no_liquidity
    )

    return Event(
        event_id="test_event",
        title="Test Event",
        description="Test description",
        markets=[yes_market, no_market],
        category="test"
    )

async def test_detector():
    """Test the detector basic functionality"""
    # Create mock client
    class MockClient:
        async def get_all_active_events(self):
            return []

    client = MockClient()
    detector = IntraMarketArbitrageDetector(client)

    print("Testing arbitrage detector...")

    # Test 1: Overpriced opportunity
    print("\n1. Testing OVERPRICED opportunity (YES=0.55, NO=0.50, sum=1.05)")
    event = create_test_event(0.55, 0.50)
    opp = await detector.analyze_event(event)

    if opp:
        print(f"   ✓ Detected: {opp.arbitrage_type}")
        print(f"   Spread: {opp.spread:.2%}")
        print(f"   Net profit: {opp.net_profit_pct:.2%}")
        print(f"   Confidence: {opp.confidence_score:.3f}")
        assert opp.arbitrage_type == "OVERPRICED"
        assert abs(opp.spread - 0.05) < 0.001
    else:
        print("   ✗ Failed to detect opportunity")
        return False

    # Test 2: Underpriced opportunity
    print("\n2. Testing UNDERPRICED opportunity (YES=0.45, NO=0.48, sum=0.93)")
    event = create_test_event(0.45, 0.48)
    opp = await detector.analyze_event(event)

    if opp:
        print(f"   ✓ Detected: {opp.arbitrage_type}")
        print(f"   Spread: {opp.spread:.2%}")
        print(f"   Net profit: {opp.net_profit_pct:.2%}")
        assert opp.arbitrage_type == "UNDERPRICED"
        assert abs(opp.spread - 0.07) < 0.001
    else:
        print("   ✗ Failed to detect opportunity")
        return False

    # Test 3: Below threshold
    print("\n3. Testing below threshold (YES=0.51, NO=0.50, sum=1.01, spread=1%)")
    event = create_test_event(0.51, 0.50)
    opp = await detector.analyze_event(event)

    if opp is None:
        print("   ✓ Correctly rejected (below 3% threshold)")
    else:
        print(f"   ✗ Should have been rejected (spread={opp.spread:.2%})")
        return False

    # Test 4: Insufficient liquidity
    print("\n4. Testing insufficient liquidity")
    event = create_test_event(0.55, 0.50, yes_liquidity=100.0, no_liquidity=100.0)
    opp = await detector.analyze_event(event)

    if opp is None:
        print("   ✓ Correctly rejected (insufficient liquidity)")
    else:
        print("   ✗ Should have been rejected (low liquidity)")
        return False

    # Test 5: Invalid prices
    print("\n5. Testing invalid prices")
    event = create_test_event(0.0, 0.50)  # Invalid: price = 0
    opp = await detector.analyze_event(event)

    if opp is None:
        print("   ✓ Correctly rejected (invalid price)")
    else:
        print("   ✗ Should have been rejected (price=0)")
        return False

    # Test 6: Profit calculation
    print("\n6. Testing profit calculation accuracy")
    event = create_test_event(0.54, 0.50)
    opp = await detector.analyze_event(event)

    if opp:
        print(f"   Spread: {opp.spread:.2%}")
        print(f"   Expected profit (gross): ${opp.expected_profit_usd:.2f}")
        print(f"   Fees: ${opp.estimated_fees:.2f}")
        print(f"   Slippage: ${opp.estimated_slippage:.2f}")
        print(f"   Net profit %: {opp.net_profit_pct:.2%}")

        # Verify net < gross
        if opp.net_profit_pct < opp.expected_profit_pct:
            print("   ✓ Net profit correctly less than gross")
        else:
            print("   ✗ Net profit should be less than gross")
            return False
    else:
        print("   ✗ Should have detected opportunity")
        return False

    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60)
    return True

if __name__ == "__main__":
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(test_detector())
    sys.exit(0 if result else 1)
