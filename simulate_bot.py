#!/usr/bin/env python3
"""
simulate_bot.py - Main entry point for the simulated trading bot.

This bot operates differently from the main trading bot:
- Uses simulated balance instead of real account
- Posts trading signals to Telegram signal group
- Sends completion notifications when trades finish
- Never executes real trades
"""

import sys
import os
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.env_loader import load_environment
from src.utils.logging_config import setup_logging
from src.models.config_models import TradingConfig
from src.simulated_trading_bot import SimulatedTradingBot


def simulate_bot(run_once: bool = False) -> None:
    """
    Main function to run the simulated trading bot.
    
    Args:
        run_once: If True, run one simulation cycle and exit. If False, run continuously.
    """
    try:
        print("🎯 Starting Simulated Trading Bot...")
        
        # Load environment variables
        load_environment()
        
        # Load configuration
        config = TradingConfig.from_env()
        
        # Validate simulation mode is enabled
        if not config.simulation_mode:
            print("⚠️ SIMULATION_MODE is not enabled in .env file. Setting simulation_mode=True for this run.")
            config.simulation_mode = True
        
        # Setup logging with simulation-specific log file
        simulation_log_file = config.get_mode_specific_log_file()
        setup_logging(level=config.log_level, log_file=simulation_log_file)
        print(f"📝 Logging to: {simulation_log_file}")
        
        # Validate required configuration
        if not config.api_key or not config.api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET are required even for simulation")
        
        if not config.symbols:
            raise ValueError("No trading symbols configured")
        
        print(f"✅ Configuration loaded:")
        print(f"   Trading Symbols: {len(config.symbols)} symbols")
        print(f"   Fixed Trade Value: ${config.simulation_fixed_trade_value:.2f}")
        print(f"   Balance: Unlimited")
        print(f"   Telegram Notifications: {'✅ Enabled' if config.enable_telegram_notifications else '❌ Disabled'}")
        print(f"   Testnet Mode: {'✅ Enabled' if config.testnet else '❌ Disabled'}")
        
        # Initialize the simulated trading bot
        bot = SimulatedTradingBot(config)
        
        if run_once:
            print("🔄 Running single simulation cycle...")
            bot.run_simulation_cycle()
            
            # Show final performance
            performance = bot.get_performance_summary()
            print("\n" + "="*60)
            print("📊 SIMULATION CYCLE COMPLETED")
            print("="*60)
            print(f"Total P&L: ${performance['total_pnl']:+.2f}")
            print(f"Active Positions: {performance['active_positions']}")
            print(f"Completed Trades: {performance['total_trades']}")
            if performance['total_trades'] > 0:
                print(f"Win Rate: {performance['win_rate']:.1f}%")
        else:
            print("🚀 Starting continuous simulation...")
            print("Press Ctrl+C to stop the simulation")
            
            # Run continuous simulation
            bot.run_continuous_simulation(scan_interval=config.scan_interval)
        
    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user")
    except Exception as e:
        print(f"\n❌ Error in simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Simulated Trading Bot - Trade with virtual balance and Telegram notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run continuous simulation
  %(prog)s --once             # Run single simulation cycle
  %(prog)s --help             # Show this help message

Environment Variables Required:
  SIMULATION_MODE=true        # Enable simulation mode
  SIMULATION_BALANCE=10000.0  # Starting virtual balance
  
  # Telegram Notifications
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_SIGNAL_GROUP_ID=...
  ENABLE_TELEGRAM_NOTIFICATIONS=true
  
  # Binance API (for market data only)
  BINANCE_API_KEY=...
  BINANCE_API_SECRET=...
  USE_TESTNET=true
        """
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run single simulation cycle and exit (useful for testing)'
    )
    
    parser.add_argument(
        '--balance',
        type=float,
        help='Override simulation balance (default: from SIMULATION_BALANCE env var)'
    )
    
    args = parser.parse_args()
    
    # Override environment variable if balance specified
    if args.balance:
        os.environ['SIMULATION_BALANCE'] = str(args.balance)
        print(f"💰 Using custom simulation balance: ${args.balance:,.2f}")
    
    # Run the simulation
    simulate_bot(run_once=args.once)


if __name__ == "__main__":
    main()