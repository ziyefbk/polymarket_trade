"""
On-Chain Intelligence Analyzer for Polymarket Trading

This module monitors blockchain activity related to Polymarket:
- Tracks large USDC transactions and wallet movements
- Monitors Polymarket smart contract interactions
- Identifies whale addresses and their betting patterns
- Detects sudden liquidity changes
- Analyzes on-chain order book depth
- Tracks CTF (Conditional Tokens Framework) transfers

This provides the most reliable signal - real money on the blockchain.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger

try:
    from web3 import Web3
    from web3.contract import Contract
    from web3.types import BlockData, TxData
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("Web3 not available. Install: pip install web3")


# Polymarket Contract Addresses on Polygon
POLYMARKET_CONTRACTS = {
    "CTF": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",  # Conditional Tokens Framework
    "CTF_EXCHANGE": "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",  # Exchange
    "NEG_RISK_CTF_EXCHANGE": "0xC5d563A36AE78145C45a50134d48A1215220f80a",  # Neg Risk Exchange
    "NEG_RISK_ADAPTER": "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296",  # Neg Risk Adapter
}

# USDC Contract on Polygon
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC (6 decimals)

# Whale threshold (>= $10,000 USDC)
WHALE_THRESHOLD = 10000


@dataclass
class OnChainTransaction:
    """Represents a blockchain transaction"""
    tx_hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    value: float  # In USDC
    token_ids: List[str] = field(default_factory=list)
    transaction_type: str = ""  # "DEPOSIT", "WITHDRAW", "BUY", "SELL", "TRANSFER"
    gas_used: int = 0
    gas_price: float = 0


@dataclass
class WhaleWallet:
    """Represents a whale wallet"""
    address: str
    total_volume: float
    transaction_count: int
    avg_transaction_size: float
    first_seen: datetime
    last_seen: datetime
    betting_pattern: Dict[str, float] = field(default_factory=dict)  # token_id -> volume
    win_rate: float = 0.0  # If calculable


@dataclass
class LiquidityChange:
    """Represents a liquidity change event"""
    token_id: str
    event_id: str
    event_title: str
    old_liquidity: float
    new_liquidity: float
    change_amount: float
    change_percent: float
    timestamp: datetime
    trigger_tx: Optional[str] = None


@dataclass
class OnChainIntelligence:
    """Intelligence report from on-chain analysis"""
    time_period_start: datetime
    time_period_end: datetime
    total_transactions: int
    total_volume: float
    unique_addresses: int
    whale_transactions: int
    whale_volume: float
    top_whales: List[WhaleWallet]
    large_deposits: List[OnChainTransaction]
    large_withdrawals: List[OnChainTransaction]
    liquidity_changes: List[LiquidityChange]
    hot_tokens: List[Dict[str, Any]]  # Tokens with high activity
    network_stats: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)


class OnChainIntelligenceAnalyzer:
    """
    Monitors Polygon blockchain for Polymarket-related activity.

    Features:
    - Whale wallet tracking
    - Large transaction detection
    - Liquidity monitoring
    - Smart contract event parsing
    - Transaction pattern analysis
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        usdc_threshold: float = WHALE_THRESHOLD
    ):
        """
        Initialize on-chain analyzer.

        Args:
            rpc_url: Polygon RPC endpoint (default: uses public endpoint)
            usdc_threshold: Minimum USDC amount to consider as "whale" transaction
        """
        if not WEB3_AVAILABLE:
            raise ImportError(
                "On-chain analysis requires web3. Install with: pip install web3"
            )

        # Use public Polygon RPC if not provided
        self.rpc_url = rpc_url or "https://polygon-rpc.com"
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.usdc_threshold = usdc_threshold

        # Check connection
        if not self.w3.is_connected():
            logger.warning(f"Failed to connect to Polygon RPC: {self.rpc_url}")
        else:
            logger.info(f"Connected to Polygon network (Chain ID: {self.w3.eth.chain_id})")

        # Contract ABIs (simplified - in production, use full ABIs)
        self.usdc_abi = self._get_erc20_abi()
        self.ctf_abi = self._get_ctf_abi()

        # Initialize contracts
        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS),
            abi=self.usdc_abi
        )

        logger.info(f"OnChainIntelligenceAnalyzer initialized (whale threshold: ${usdc_threshold:,.0f})")

    def _get_erc20_abi(self) -> List[Dict]:
        """Get minimal ERC20 ABI for USDC"""
        return [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "from", "type": "address"},
                    {"indexed": True, "name": "to", "type": "address"},
                    {"indexed": False, "name": "value", "type": "uint256"}
                ],
                "name": "Transfer",
                "type": "event"
            }
        ]

    def _get_ctf_abi(self) -> List[Dict]:
        """Get minimal CTF ABI"""
        return [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "from", "type": "address"},
                    {"indexed": True, "name": "to", "type": "address"},
                    {"indexed": False, "name": "id", "type": "uint256"},
                    {"indexed": False, "name": "value", "type": "uint256"}
                ],
                "name": "TransferSingle",
                "type": "event"
            }
        ]

    async def get_usdc_balance(self, address: str) -> float:
        """
        Get USDC balance for an address.

        Args:
            address: Ethereum address

        Returns:
            USDC balance (adjusted for 6 decimals)
        """
        try:
            checksum_address = Web3.to_checksum_address(address)
            balance_wei = self.usdc_contract.functions.balanceOf(checksum_address).call()
            # USDC has 6 decimals
            balance = balance_wei / 1e6
            return balance
        except Exception as e:
            logger.error(f"Failed to get USDC balance for {address}: {e}")
            return 0.0

    async def monitor_large_transactions(
        self,
        from_block: int,
        to_block: Optional[int] = None,
        min_amount: Optional[float] = None
    ) -> List[OnChainTransaction]:
        """
        Monitor large USDC transactions between blocks.

        Args:
            from_block: Starting block number
            to_block: Ending block number (default: latest)
            min_amount: Minimum USDC amount (default: whale threshold)

        Returns:
            List of large OnChainTransaction objects
        """
        if not to_block:
            to_block = self.w3.eth.block_number

        min_amount = min_amount or self.usdc_threshold

        logger.info(
            f"Monitoring USDC transfers from block {from_block} to {to_block} "
            f"(min amount: ${min_amount:,.0f})"
        )

        try:
            # Get Transfer events from USDC contract
            transfer_filter = self.usdc_contract.events.Transfer.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )

            events = transfer_filter.get_all_entries()
            logger.info(f"Found {len(events)} USDC transfer events")

            large_txs = []

            for event in events:
                # Convert USDC amount (6 decimals)
                amount = event['args']['value'] / 1e6

                if amount >= min_amount:
                    # Get transaction details
                    tx_hash = event['transactionHash'].hex()
                    tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                    block = self.w3.eth.get_block(event['blockNumber'])

                    tx = OnChainTransaction(
                        tx_hash=tx_hash,
                        block_number=event['blockNumber'],
                        timestamp=datetime.fromtimestamp(block['timestamp']),
                        from_address=event['args']['from'],
                        to_address=event['args']['to'],
                        value=amount,
                        gas_used=tx_receipt['gasUsed'],
                        gas_price=tx_receipt['effectiveGasPrice'] / 1e18  # Convert to MATIC
                    )

                    # Determine transaction type
                    tx.transaction_type = self._classify_transaction(tx)

                    large_txs.append(tx)

            logger.info(f"Found {len(large_txs)} large transactions (>= ${min_amount:,.0f})")
            return large_txs

        except Exception as e:
            logger.error(f"Failed to monitor transactions: {e}")
            return []

    def _classify_transaction(self, tx: OnChainTransaction) -> str:
        """Classify transaction type based on addresses"""
        polymarket_addresses = set(POLYMARKET_CONTRACTS.values())

        from_is_pm = tx.from_address.lower() in {a.lower() for a in polymarket_addresses}
        to_is_pm = tx.to_address.lower() in {a.lower() for a in polymarket_addresses}

        if to_is_pm and not from_is_pm:
            return "DEPOSIT"
        elif from_is_pm and not to_is_pm:
            return "WITHDRAW"
        elif from_is_pm and to_is_pm:
            return "INTERNAL"
        else:
            return "TRANSFER"

    async def identify_whale_wallets(
        self,
        transactions: List[OnChainTransaction]
    ) -> List[WhaleWallet]:
        """
        Identify whale wallets from transaction list.

        Args:
            transactions: List of transactions to analyze

        Returns:
            List of WhaleWallet objects, sorted by volume
        """
        # Aggregate by address
        wallet_stats = defaultdict(lambda: {
            'volume': 0.0,
            'count': 0,
            'first_seen': None,
            'last_seen': None
        })

        for tx in transactions:
            # Count both sender and receiver
            for addr in [tx.from_address, tx.to_address]:
                stats = wallet_stats[addr]
                stats['volume'] += tx.value
                stats['count'] += 1

                if not stats['first_seen'] or tx.timestamp < stats['first_seen']:
                    stats['first_seen'] = tx.timestamp
                if not stats['last_seen'] or tx.timestamp > stats['last_seen']:
                    stats['last_seen'] = tx.timestamp

        # Create WhaleWallet objects
        whales = []
        for address, stats in wallet_stats.items():
            if stats['volume'] >= self.usdc_threshold:
                whale = WhaleWallet(
                    address=address,
                    total_volume=stats['volume'],
                    transaction_count=stats['count'],
                    avg_transaction_size=stats['volume'] / stats['count'],
                    first_seen=stats['first_seen'],
                    last_seen=stats['last_seen']
                )
                whales.append(whale)

        # Sort by volume
        whales.sort(key=lambda w: w.total_volume, reverse=True)

        logger.info(f"Identified {len(whales)} whale wallets")
        return whales

    async def get_recent_activity(
        self,
        hours: int = 24,
        min_amount: Optional[float] = None
    ) -> OnChainIntelligence:
        """
        Get recent on-chain activity summary.

        Args:
            hours: How many hours of history to analyze
            min_amount: Minimum transaction amount to consider

        Returns:
            OnChainIntelligence report
        """
        logger.info(f"Analyzing on-chain activity for last {hours} hours")

        # Calculate block range
        # Polygon: ~2 second block time
        blocks_per_hour = 1800  # 3600 / 2
        block_range = hours * blocks_per_hour

        current_block = self.w3.eth.block_number
        from_block = max(0, current_block - block_range)

        # Get transactions
        transactions = await self.monitor_large_transactions(
            from_block=from_block,
            to_block=current_block,
            min_amount=min_amount
        )

        if not transactions:
            logger.warning("No transactions found in the specified period")
            return None

        # Time range
        time_start = min(tx.timestamp for tx in transactions)
        time_end = max(tx.timestamp for tx in transactions)

        # Basic stats
        total_volume = sum(tx.value for tx in transactions)
        unique_addresses = len(set(
            [tx.from_address for tx in transactions] +
            [tx.to_address for tx in transactions]
        ))

        # Whale analysis
        whale_txs = [tx for tx in transactions if tx.value >= self.usdc_threshold]
        whale_volume = sum(tx.value for tx in whale_txs)
        whales = await self.identify_whale_wallets(transactions)

        # Separate deposits and withdrawals
        deposits = [tx for tx in transactions if tx.transaction_type == "DEPOSIT"]
        withdrawals = [tx for tx in transactions if tx.transaction_type == "WITHDRAW"]

        # Sort by value
        deposits.sort(key=lambda tx: tx.value, reverse=True)
        withdrawals.sort(key=lambda tx: tx.value, reverse=True)

        # Network stats
        total_gas = sum(tx.gas_used * tx.gas_price for tx in transactions)
        avg_gas = total_gas / len(transactions) if transactions else 0

        network_stats = {
            "total_gas_used": sum(tx.gas_used for tx in transactions),
            "total_gas_cost_matic": total_gas,
            "avg_gas_cost_matic": avg_gas,
            "block_range": (from_block, current_block),
            "blocks_analyzed": current_block - from_block
        }

        # Create report
        report = OnChainIntelligence(
            time_period_start=time_start,
            time_period_end=time_end,
            total_transactions=len(transactions),
            total_volume=total_volume,
            unique_addresses=unique_addresses,
            whale_transactions=len(whale_txs),
            whale_volume=whale_volume,
            top_whales=whales[:10],  # Top 10
            large_deposits=deposits[:10],
            large_withdrawals=withdrawals[:10],
            liquidity_changes=[],  # Would need more complex analysis
            hot_tokens=[],  # Would need token transfer parsing
            network_stats=network_stats
        )

        logger.info(
            f"On-chain report generated: {len(transactions)} txs, "
            f"${total_volume:,.0f} volume, {len(whales)} whales"
        )

        return report

    def print_report(self, report: OnChainIntelligence):
        """Print on-chain intelligence report"""
        print("\n" + "="*80)
        print("ON-CHAIN INTELLIGENCE REPORT")
        print("="*80)
        print(f"Period: {report.time_period_start} to {report.time_period_end}")
        print(f"Generated: {report.generated_at}")
        print("\n" + "-"*80)
        print("NETWORK ACTIVITY")
        print("-"*80)
        print(f"Total Transactions: {report.total_transactions:,}")
        print(f"Total Volume: ${report.total_volume:,.2f} USDC")
        print(f"Unique Addresses: {report.unique_addresses:,}")
        print(f"Avg Transaction Size: ${report.total_volume/report.total_transactions:,.2f}")

        print(f"\nWhale Activity (>= ${self.usdc_threshold:,.0f}):")
        print(f"  Whale Transactions: {report.whale_transactions:,}")
        print(f"  Whale Volume: ${report.whale_volume:,.2f} ({report.whale_volume/report.total_volume*100:.1f}% of total)")

        print("\n" + "-"*80)
        print("TOP WHALE WALLETS")
        print("-"*80)
        for i, whale in enumerate(report.top_whales[:5], 1):
            print(f"\n{i}. {whale.address[:10]}...{whale.address[-8:]}")
            print(f"   Total Volume: ${whale.total_volume:,.2f}")
            print(f"   Transactions: {whale.transaction_count}")
            print(f"   Avg Size: ${whale.avg_transaction_size:,.2f}")
            print(f"   Last Active: {whale.last_seen}")

        print("\n" + "-"*80)
        print("LARGE DEPOSITS (Top 5)")
        print("-"*80)
        for i, tx in enumerate(report.large_deposits[:5], 1):
            print(f"\n{i}. ${tx.value:,.2f} USDC")
            print(f"   From: {tx.from_address[:10]}...{tx.from_address[-8:]}")
            print(f"   Time: {tx.timestamp}")
            print(f"   Tx: {tx.tx_hash[:20]}...")

        print("\n" + "-"*80)
        print("LARGE WITHDRAWALS (Top 5)")
        print("-"*80)
        for i, tx in enumerate(report.large_withdrawals[:5], 1):
            print(f"\n{i}. ${tx.value:,.2f} USDC")
            print(f"   To: {tx.to_address[:10]}...{tx.to_address[-8:]}")
            print(f"   Time: {tx.timestamp}")
            print(f"   Tx: {tx.tx_hash[:20]}...")

        print("\n" + "-"*80)
        print("NETWORK STATISTICS")
        print("-"*80)
        print(f"Blocks Analyzed: {report.network_stats['blocks_analyzed']:,}")
        print(f"Total Gas Used: {report.network_stats['total_gas_used']:,}")
        print(f"Total Gas Cost: {report.network_stats['total_gas_cost_matic']:.4f} MATIC")
        print(f"Avg Gas Cost/Tx: {report.network_stats['avg_gas_cost_matic']:.6f} MATIC")

        print("\n" + "="*80)

    async def track_wallet_in_realtime(
        self,
        wallet_address: str,
        callback: Optional[callable] = None,
        poll_interval: int = 10
    ):
        """
        Track a wallet in real-time for new transactions.

        Args:
            wallet_address: Wallet to track
            callback: Function to call when new transaction detected
            poll_interval: Seconds between checks
        """
        logger.info(f"Starting real-time tracking for {wallet_address}")

        last_block = self.w3.eth.block_number

        while True:
            try:
                current_block = self.w3.eth.block_number

                if current_block > last_block:
                    # Check for new transactions
                    txs = await self.monitor_large_transactions(
                        from_block=last_block + 1,
                        to_block=current_block,
                        min_amount=0  # Track all amounts
                    )

                    # Filter for target wallet
                    wallet_txs = [
                        tx for tx in txs
                        if tx.from_address.lower() == wallet_address.lower() or
                           tx.to_address.lower() == wallet_address.lower()
                    ]

                    if wallet_txs:
                        logger.info(f"Found {len(wallet_txs)} new transactions for {wallet_address}")

                        if callback:
                            for tx in wallet_txs:
                                await callback(tx)
                        else:
                            for tx in wallet_txs:
                                print(f"\n🔔 New Transaction:")
                                print(f"   Amount: ${tx.value:,.2f}")
                                print(f"   Type: {tx.transaction_type}")
                                print(f"   Tx: {tx.tx_hash}")

                    last_block = current_block

            except Exception as e:
                logger.error(f"Error in real-time tracking: {e}")

            await asyncio.sleep(poll_interval)


# Convenience function
async def get_polymarket_onchain_activity(hours: int = 24, min_amount: float = 10000):
    """
    Quick function to get Polymarket on-chain activity.

    Args:
        hours: Hours of history to analyze
        min_amount: Minimum transaction amount

    Returns:
        OnChainIntelligence report
    """
    analyzer = OnChainIntelligenceAnalyzer()
    return await analyzer.get_recent_activity(hours=hours, min_amount=min_amount)
