#!/usr/bin/env python3
"""
Main entry point for the refactored trading bot.
Follows SOLID principles and clean architecture.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.trading_bot import TradingBot
from src.utils import load_config, setup_logging


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Enhanced Trading Bot - Quality over Quantity')
    parser.add_argument(
        '--continuous', 
        action='store_true', 
        help='Run in continuous mode with internal loop (legacy mode)'
    )
    parser.add_argument(
        '--version', 
        action='version', 
        version='Trading Bot v2.0.0 - Enhanced Quality over Quantity'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging with mode-specific log file
        log_file = config.log_file or config.get_mode_specific_log_file()
        setup_logging(
            level=config.log_level,
            log_file=log_file
        )
        
        # Create trading bot
        bot = TradingBot(config)
        
        # Start bot in appropriate mode
        if args.continuous:
            print("🔄 Starting bot in CONTINUOUS mode (internal loop)")
            bot.start_continuous()
        else:
            print("🎯 Starting bot in SCHEDULED mode (single execution)")
            bot.start()
        
    except Exception as e:
        print(f"Failed to start trading bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
