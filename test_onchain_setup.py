#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
On-Chain Intelligence Setup Test
测试链上数据监控配置
"""
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_web3_import():
    """Test if web3 is installed"""
    print("Testing web3 import...")

    try:
        from web3 import Web3
        print("  PASS: web3 imported successfully")
        return True
    except ImportError:
        print("  FAIL: web3 not installed")
        print("  Install: pip install web3")
        return False

def test_polygon_connection():
    """Test connection to Polygon network"""
    print("\nTesting Polygon network connection...")

    try:
        from web3 import Web3

        # Try public endpoint
        rpc_url = "https://polygon-rpc.com"
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if w3.is_connected():
            chain_id = w3.eth.chain_id
            block_number = w3.eth.block_number

            print(f"  PASS: Connected to Polygon")
            print(f"    Chain ID: {chain_id}")
            print(f"    Latest Block: {block_number:,}")
            return True
        else:
            print("  FAIL: Cannot connect to Polygon")
            print("  Try using Alchemy or Infura RPC endpoint")
            return False

    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_usdc_contract():
    """Test USDC contract interaction"""
    print("\nTesting USDC contract...")

    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

        if not w3.is_connected():
            print("  SKIP: Not connected to network")
            return False

        # USDC contract address on Polygon
        usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

        # Simple ABI for balanceOf
        abi = [{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]

        usdc_contract = w3.eth.contract(
            address=Web3.to_checksum_address(usdc_address),
            abi=abi
        )

        # Test with a known address (Polymarket exchange)
        test_address = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
        balance_wei = usdc_contract.functions.balanceOf(
            Web3.to_checksum_address(test_address)
        ).call()

        balance = balance_wei / 1e6  # USDC has 6 decimals

        print(f"  PASS: USDC contract accessible")
        print(f"    Test address balance: ${balance:,.2f}")
        return True

    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_integration_module():
    """Test if on-chain integration module loads"""
    print("\nTesting on-chain integration module...")

    try:
        from src.analyzer.onchain_intelligence import (
            OnChainIntelligenceAnalyzer,
            OnChainTransaction,
            WhaleWallet,
            WEB3_AVAILABLE
        )

        if WEB3_AVAILABLE:
            print("  PASS: On-chain module loaded")

            # Try to initialize
            analyzer = OnChainIntelligenceAnalyzer()
            print(f"  PASS: Analyzer initialized")
            print(f"    Whale threshold: ${analyzer.usdc_threshold:,.0f}")

            return True
        else:
            print("  FAIL: Web3 not available")
            return False

    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_async_functionality():
    """Test async functions"""
    print("\nTesting async functionality...")

    try:
        import asyncio
        from src.analyzer.onchain_intelligence import OnChainIntelligenceAnalyzer

        async def test():
            analyzer = OnChainIntelligenceAnalyzer()

            # Test balance query
            test_address = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
            balance = await analyzer.get_usdc_balance(test_address)

            print(f"  PASS: Async functions work")
            print(f"    Balance query successful: ${balance:,.2f}")
            return True

        result = asyncio.run(test())
        return result

    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def main():
    print("="*60)
    print("On-Chain Intelligence Setup Test")
    print("="*60)

    results = {
        "Web3 import": test_web3_import(),
        "Polygon connection": test_polygon_connection(),
        "USDC contract": test_usdc_contract(),
        "Integration module": test_integration_module(),
        "Async functionality": test_async_functionality(),
    }

    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("SUCCESS: On-chain integration is ready!")
        print("\nNext steps:")
        print("1. Run example: python examples\\onchain_integration_example.py")
        print("2. Read docs: docs\\ONCHAIN_INTEGRATION.md")
        print("\nOptional: Get faster RPC access:")
        print("- Alchemy: https://www.alchemy.com/ (recommended)")
        print("- Infura: https://infura.io/")
    else:
        print("WARNING: Some tests failed. Fix the issues above.")
        print("\nQuick fixes:")
        print("1. Install web3: pip install web3")
        print("2. Check internet connection")
        print("3. Try different RPC endpoint if connection fails")
    print("="*60)

if __name__ == "__main__":
    main()
