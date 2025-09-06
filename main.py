#!/usr/bin/env python3
"""
Main entry point for the refactored trading bot.
Follows SOLID principles and clean architecture.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.trading_bot import TradingBot
from src.utils import load_config, setup_logging


def main():
    """Main entry point."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging with mode-specific log file
        log_file = config.log_file or config.get_mode_specific_log_file()
        setup_logging(
            level=config.log_level,
            log_file=log_file
        )
        
        # Create and start trading bot
        bot = TradingBot(config)
        bot.start()
        
    except Exception as e:
        print(f"Failed to start trading bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
