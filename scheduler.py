#!/usr/bin/env python3
"""
Trading Bot Scheduler - Optimal 4H Candle Timing
Runs bot at: 03:05, 07:05, 11:05, 15:05, 19:05, 23:05 (Vietnam time)
"""

import schedule
import time
import subprocess
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Set up logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration
TRADING_BOT_DIR = Path(__file__).parent
TIMEOUT_SECONDS = 300  # 5 minutes timeout
MAX_RETRIES = 2

def run_trading_bot():
    """Run the enhanced trading bot with timeout and error handling."""
    start_time = datetime.now()
    logger.info("🚀" + "="*60)
    logger.info(f"🚀 SCHEDULED TRADING BOT RUN - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("🚀" + "="*60)
    
    try:
        # Change to bot directory
        os.chdir(TRADING_BOT_DIR)
        
        # Run bot with timeout
        cmd = ['timeout', f'{TIMEOUT_SECONDS}s', 'uv', 'run', 'python', 'main.py']
        logger.info(f"📋 Executing: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 30  # Extra timeout buffer
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log results
        if result.returncode == 0:
            logger.info(f"✅ Trading bot completed successfully in {duration:.1f}s")
            if result.stdout:
                logger.info("📊 Bot output summary:")
                # Log last few lines of output
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:  # Last 10 lines
                    if line.strip():
                        logger.info(f"   {line}")
        
        elif result.returncode == 124:  # Timeout exit code
            logger.warning(f"⏰ Trading bot timed out after {TIMEOUT_SECONDS}s")
            
        else:
            logger.warning(f"⚠️ Trading bot exited with code: {result.returncode}")
            if result.stderr:
                logger.error(f"Error output: {result.stderr}")
        
        # Always log some output for monitoring
        logger.info(f"📈 Run completed in {duration:.1f}s")
        logger.info("🏁" + "="*60)
        
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Trading bot execution timed out after {TIMEOUT_SECONDS + 30}s")
    except Exception as e:
        logger.error(f"❌ Error running trading bot: {e}")
        logger.exception("Full error details:")

def run_with_retry():
    """Run trading bot with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            logger.info(f"🔄 Retry attempt {attempt}/{MAX_RETRIES}")
            time.sleep(30)  # Wait 30 seconds between retries
        
        try:
            run_trading_bot()
            break  # Success, exit retry loop
        except Exception as e:
            logger.error(f"❌ Attempt {attempt} failed: {e}")
            if attempt == MAX_RETRIES:
                logger.error("💥 All retry attempts exhausted")

def check_system_health():
    """Check basic system health before running."""
    try:
        # Check if uv is available
        result = subprocess.run(['uv', '--version'], capture_output=True)
        if result.returncode != 0:
            logger.error("❌ UV package manager not available")
            return False
        
        # Check if main.py exists
        if not (TRADING_BOT_DIR / 'main.py').exists():
            logger.error("❌ main.py not found in trading bot directory")
            return False
        
        # Check disk space
        import shutil
        _, _, free = shutil.disk_usage(TRADING_BOT_DIR)
        free_gb = free // (1024**3)
        if free_gb < 1:
            logger.warning(f"⚠️ Low disk space: {free_gb}GB free")
        
        logger.info(f"✅ System health check passed - {free_gb}GB free disk space")
        return True
        
    except Exception as e:
        logger.error(f"❌ System health check failed: {e}")
        return False

def main():
    """Main scheduler function."""
    logger.info("📅" + "="*60)
    logger.info("📅 ENHANCED TRADING BOT SCHEDULER STARTED")
    logger.info("📅" + "="*60)
    logger.info("⏰ Optimal 4H Candle Schedule (Vietnam Time UTC+7):")
    logger.info("   • 03:05 AM - After 03:00 candle close")
    logger.info("   • 07:05 AM - After 07:00 candle close") 
    logger.info("   • 11:05 AM - After 11:00 candle close")
    logger.info("   • 15:05 PM - After 15:00 candle close")
    logger.info("   • 19:05 PM - After 19:00 candle close")
    logger.info("   • 23:05 PM - After 23:00 candle close")
    logger.info("💡 5-minute delay ensures complete data synchronization")
    logger.info("🎯 Focus: 'Quality over Quantity' - Enhanced R:R Strategy")
    logger.info("📅" + "="*60)
    
    # System health check
    if not check_system_health():
        logger.error("❌ System health check failed - exiting")
        sys.exit(1)
    
    # Schedule trading bot runs at optimal times
    schedule.every().day.at("03:05").do(run_with_retry)
    schedule.every().day.at("07:05").do(run_with_retry) 
    schedule.every().day.at("11:05").do(run_with_retry)
    schedule.every().day.at("15:05").do(run_with_retry)
    schedule.every().day.at("19:05").do(run_with_retry)
    schedule.every().day.at("23:05").do(run_with_retry)
    
    # Log next scheduled run
    try:
        next_run = schedule.next_run()
        if next_run:
            logger.info(f"⏰ Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    except:
        logger.info("⏰ Scheduler active - waiting for next run time")
    
    logger.info("🔄 Scheduler loop started - checking every minute")
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
        raise

if __name__ == "__main__":
    main()
