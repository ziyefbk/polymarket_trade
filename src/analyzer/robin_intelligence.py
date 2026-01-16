"""
Robin Intelligence Integration for Polymarket Arbitrage System

This module integrates the Robin dark web OSINT tool to gather intelligence
that can inform prediction market trading decisions.

Use cases:
- Detect early signals of major events from dark web chatter
- Identify potential market-moving information before public disclosure
- Correlate dark web activity with prediction market outcomes
"""
import sys
import os
import asyncio
import subprocess
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
from loguru import logger

# Add robin_signals to path
ROBIN_PATH = Path(__file__).parent.parent.parent / "robin_signals"
sys.path.insert(0, str(ROBIN_PATH))

try:
    from robin_signals.search import get_search_results
    from robin_signals.scrape import scrape_multiple
    from robin_signals.llm import get_llm, refine_query, filter_results, generate_summary
    ROBIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Robin integration not available: {e}")
    ROBIN_AVAILABLE = False


class RobinIntelligenceAnalyzer:
    """
    Integrates Robin dark web OSINT tool for intelligence gathering.

    This analyzer can search the dark web for information related to:
    - Political events (elections, policy changes)
    - Security incidents (data breaches, cyberattacks)
    - Economic indicators (cryptocurrency markets, financial crimes)
    - Geopolitical events (conflicts, sanctions)

    The intelligence is then used to inform trading decisions on Polymarket.
    """

    def __init__(self, model: str = "gpt-4o", threads: int = 5):
        """
        Initialize Robin intelligence analyzer.

        Args:
            model: LLM model to use (gpt4o, claude-3-5-sonnet-latest, etc.)
            threads: Number of threads for scraping
        """
        if not ROBIN_AVAILABLE:
            raise ImportError(
                "Robin integration not available. "
                "Ensure robin_signals directory is present and dependencies installed."
            )

        self.model = model
        self.threads = threads
        self.llm = None

        # Check if Tor is running
        self._check_tor_status()

        logger.info(f"RobinIntelligenceAnalyzer initialized with model={model}, threads={threads}")

    def _check_tor_status(self) -> bool:
        """
        Check if Tor is running (required for dark web access).

        Returns:
            True if Tor is running, False otherwise
        """
        try:
            # Try to connect to Tor SOCKS proxy
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 9050))
            sock.close()

            if result == 0:
                logger.info("✓ Tor is running")
                return True
            else:
                logger.warning("⚠ Tor is not running. Dark web searches will not work.")
                logger.warning("Start Tor with: sudo service tor start (Linux) or brew services start tor (Mac)")
                return False
        except Exception as e:
            logger.error(f"Failed to check Tor status: {e}")
            return False

    def search_intelligence(
        self,
        query: str,
        save_output: bool = True,
        output_dir: str = "./intelligence_reports"
    ) -> Dict[str, Any]:
        """
        Search dark web for intelligence related to query.

        Args:
            query: Search query (e.g., "ransomware attacks", "election fraud")
            save_output: Whether to save the summary to file
            output_dir: Directory to save intelligence reports

        Returns:
            Dictionary containing:
            - success: bool
            - query: original query
            - refined_query: LLM-refined query
            - summary: intelligence summary
            - summary_file: path to saved summary (if save_output=True)
            - timestamp: when the search was conducted
            - error: error message if failed
        """
        try:
            logger.info(f"Starting Robin intelligence search for: {query}")

            # Initialize LLM
            if not self.llm:
                self.llm = get_llm(self.model)

            # Step 1: Refine query using LLM
            logger.debug("Refining query with LLM...")
            refined_query = refine_query(self.llm, query)
            logger.info(f"Refined query: {refined_query}")

            # Step 2: Search dark web
            logger.debug("Searching dark web...")
            search_results = get_search_results(
                refined_query.replace(" ", "+"),
                max_workers=self.threads
            )
            logger.info(f"Found {len(search_results)} search results")

            # Step 3: Filter results with LLM
            logger.debug("Filtering results with LLM...")
            filtered_results = filter_results(self.llm, refined_query, search_results)
            logger.info(f"Filtered to {len(filtered_results)} relevant results")

            # Step 4: Scrape content from filtered URLs
            logger.debug("Scraping content...")
            scraped_results = scrape_multiple(filtered_results, max_workers=self.threads)
            logger.info(f"Scraped {len(scraped_results)} pages")

            # Step 5: Generate intelligence summary
            logger.debug("Generating intelligence summary...")
            summary = generate_summary(self.llm, query, scraped_results)

            # Save output if requested
            summary_file = None
            if save_output:
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                summary_file = os.path.join(output_dir, f"intel_{timestamp}.md")

                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write(f"# Intelligence Report: {query}\n\n")
                    f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                    f.write(f"**Refined Query:** {refined_query}\n\n")
                    f.write("---\n\n")
                    f.write(summary)

                logger.success(f"Intelligence report saved to: {summary_file}")

            return {
                "success": True,
                "query": query,
                "refined_query": refined_query,
                "summary": summary,
                "num_results": len(search_results),
                "num_filtered": len(filtered_results),
                "num_scraped": len(scraped_results),
                "summary_file": summary_file,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.exception(f"Robin intelligence search failed: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def analyze_event_intelligence(self, event_title: str) -> Optional[Dict[str, Any]]:
        """
        Gather dark web intelligence for a specific Polymarket event.

        Args:
            event_title: Title of the Polymarket event

        Returns:
            Intelligence report dictionary or None if failed
        """
        logger.info(f"Analyzing intelligence for event: {event_title}")

        # Extract key terms from event title for search
        # Example: "Will Trump win 2024 election?" -> "Trump 2024 election"
        query = self._extract_search_terms(event_title)

        return self.search_intelligence(query)

    def _extract_search_terms(self, event_title: str) -> str:
        """
        Extract relevant search terms from event title.

        Args:
            event_title: Full event title

        Returns:
            Cleaned search query
        """
        # Remove common question words
        stopwords = ["will", "is", "are", "was", "were", "does", "do", "did", "the", "a", "an"]
        words = event_title.lower().replace("?", "").split()
        filtered = [w for w in words if w not in stopwords]

        # Take first 5-6 meaningful words
        search_terms = " ".join(filtered[:6])

        logger.debug(f"Extracted search terms: '{search_terms}' from '{event_title}'")
        return search_terms

    def batch_analyze_events(
        self,
        event_titles: List[str],
        max_concurrent: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple events concurrently (with rate limiting).

        Args:
            event_titles: List of event titles to analyze
            max_concurrent: Max concurrent searches (to avoid rate limits)

        Returns:
            List of intelligence reports
        """
        results = []

        logger.info(f"Starting batch analysis for {len(event_titles)} events")

        for i, title in enumerate(event_titles, 1):
            logger.info(f"Processing event {i}/{len(event_titles)}: {title}")

            result = self.analyze_event_intelligence(title)
            results.append(result)

            # Rate limiting between searches
            if i < len(event_titles):
                logger.debug("Waiting 5s before next search...")
                import time
                time.sleep(5)

        logger.success(f"Batch analysis complete: {len(results)} reports generated")
        return results


# Convenience function for quick usage
def search_dark_web_intelligence(query: str, model: str = "gpt-4o") -> Dict[str, Any]:
    """
    Quick function to search dark web for intelligence.

    Args:
        query: Search query
        model: LLM model to use

    Returns:
        Intelligence report dictionary
    """
    analyzer = RobinIntelligenceAnalyzer(model=model)
    return analyzer.search_intelligence(query)
