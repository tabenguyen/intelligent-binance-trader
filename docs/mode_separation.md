# Trading Mode Separation

This document explains how logs and watchlists are separated between testnet and live trading modes.

## Overview

The trading bot now automatically uses different files for logs, watchlists, and active trades based on the trading mode (testnet vs live). This separation helps prevent:

- Mixing testnet and live trading data
- Accidentally using live watchlists in testnet mode
- Log confusion between different trading environments

## File Structure

### Testnet Mode (`USE_TESTNET=true`)

```
config/watchlist_testnet.txt      # Watchlist for testnet trading
data/active_trades_testnet.json   # Active positions for testnet
logs/output_testnet.log           # Logs for testnet trading
```

### Live Mode (`USE_TESTNET=false`)

```
config/watchlist_live.txt         # Watchlist for live trading
data/active_trades_live.json      # Active positions for live trading
logs/output_live.log              # Logs for live trading
```

### Fallback Files (Legacy)

```
config/watchlist.txt              # Generic watchlist (fallback)
data/active_trades.json           # Generic active trades (fallback)
logs/output.log                   # Generic log file (fallback)
```

## Configuration

The trading mode is controlled by the `USE_TESTNET` environment variable:

```bash
# For testnet trading (default)
export USE_TESTNET=true

# For live trading (use with caution!)
export USE_TESTNET=false
```

## Mode Manager Utility

Use the mode manager script to check your current configuration:

```bash
# Show current mode and file status
uv run python scripts/mode_manager.py status

# Show help
uv run python scripts/mode_manager.py help
```

## Safety Features

1. **Live Mode Warning**: The live watchlist contains a warning comment about real money trading
2. **Conservative Live Watchlist**: Pre-configured with stable, major cryptocurrencies
3. **Separate Log Files**: Easy to distinguish between testnet and live trading logs
4. **Fallback Support**: If mode-specific files don't exist, falls back to generic files

## Migration

### From Generic to Mode-Specific Files

If you have existing data in the generic files, you can manually copy them:

```bash
# Copy existing watchlist to testnet
cp config/watchlist.txt config/watchlist_testnet.txt

# Copy existing active trades to testnet
cp data/active_trades.json data/active_trades_testnet.json

# Initialize empty live files
echo '{}' > data/active_trades_live.json
```

### Switching Modes

To switch between testnet and live:

1. **To Testnet**:

   ```bash
   export USE_TESTNET=true
   uv run python scripts/mode_manager.py status
   ```

2. **To Live** (⚠️ **USE WITH CAUTION** ⚠️):
   ```bash
   export USE_TESTNET=false
   uv run python scripts/mode_manager.py status
   ```

## File Management

### Watchlist Updates

- The bot automatically updates the appropriate watchlist file based on the current mode
- Market watcher writes to the mode-specific watchlist file
- Falls back to generic watchlist if mode-specific file doesn't exist

### Active Trades

- Each mode maintains its own active trades file
- No cross-contamination between testnet and live positions
- JSON format remains the same

### Logging

- Mode is clearly indicated in log files
- Separate log files prevent confusion
- Log rotation and management work independently for each mode

## Best Practices

1. **Always verify mode**: Use `mode_manager.py status` before trading
2. **Test in testnet first**: Always test strategies in testnet before going live
3. **Separate watchlists**: Use different symbols for testnet vs live if desired
4. **Monitor logs**: Keep an eye on the appropriate log file for your mode
5. **Backup before switching**: Backup your data before switching between modes

## Troubleshooting

### Missing Files

If mode-specific files are missing, the bot will:

1. Try to fall back to generic files
2. Create new empty files if needed
3. Log warnings about missing files

### Wrong Mode

If you're in the wrong mode:

1. Stop the bot
2. Update the `USE_TESTNET` environment variable
3. Verify with `mode_manager.py status`
4. Restart the bot

### File Permissions

Ensure the bot has read/write permissions to:

- `config/` directory
- `data/` directory
- `logs/` directory
