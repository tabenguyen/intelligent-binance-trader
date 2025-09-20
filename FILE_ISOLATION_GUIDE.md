# Simulation Bot File Isolation

## Overview

The simulation bot now uses completely separate files from the real trading bot to prevent conflicts and allow both systems to run simultaneously.

## File Separation

### Log Files

| Mode                       | File Path                    | Description             |
| -------------------------- | ---------------------------- | ----------------------- |
| **Real Trading (Live)**    | `logs/output_live.log`       | Production trading logs |
| **Real Trading (Testnet)** | `logs/output_testnet.log`    | Testnet trading logs    |
| **Simulation**             | `logs/output_simulation.log` | Simulation-only logs    |

### Active Trades / State Files

| Mode                       | File Path                            | Description                 |
| -------------------------- | ------------------------------------ | --------------------------- |
| **Real Trading (Live)**    | `data/active_trades_live.json`       | Live trading positions      |
| **Real Trading (Testnet)** | `data/active_trades_testnet.json`    | Testnet positions           |
| **Simulation**             | `data/active_trades_simulation.json` | Simulated positions & state |

## Features

### ✅ **Complete Isolation**

- Real and simulation bots never share files
- Can run simultaneously without conflicts
- No risk of simulation affecting real trades

### ✅ **State Persistence**

- Simulation state is saved after each cycle
- Balance, positions, and trade history preserved
- Automatic resume from previous session

### ✅ **Separate Logging**

- Simulation has dedicated log file
- Easy to track simulation-specific events
- No mixing of real and simulated activities

## Usage Examples

### Run Real Bot (Testnet)

```bash
# Uses: logs/output_testnet.log, data/active_trades_testnet.json
SIMULATION_MODE=false USE_TESTNET=true python main.py
```

### Run Simulation Bot

```bash
# Uses: logs/output_simulation.log, data/active_trades_simulation.json
SIMULATION_MODE=true python simulate_bot.py
```

### Run Both Simultaneously

```bash
# Terminal 1: Real bot (testnet)
SIMULATION_MODE=false USE_TESTNET=true python main.py

# Terminal 2: Simulation bot (different files)
SIMULATION_MODE=true python simulate_bot.py
```

## State Management

### Simulation State Structure

```json
{
  "balance": 1000.0,
  "initial_balance": 1000.0,
  "positions": {
    "BTCUSDT": {
      "symbol": "BTCUSDT",
      "quantity": 0.001,
      "entry_price": 43250.0,
      "entry_time": "2025-09-21T01:52:00.000000",
      "stop_loss": 41162.5,
      "take_profit": 45337.5,
      "signal_message_id": "12345"
    }
  },
  "completed_trades": [
    {
      "id": "sim_trade_001",
      "symbol": "BTCUSDT",
      "direction": "BUY",
      "quantity": 0.001,
      "entry_price": 43250.0,
      "exit_price": 43575.0,
      "entry_time": "2025-09-21T01:52:00.000000",
      "exit_time": "2025-09-21T02:15:00.000000",
      "status": "FILLED",
      "pnl": 7.5,
      "commission": 0.5,
      "strategy_name": "EMA Cross Strategy",
      "stop_loss": 41162.5,
      "take_profit": 45337.5
    }
  ],
  "timestamp": "2025-09-21T02:15:00.000000"
}
```

### Automatic Operations

- **Load State**: On bot startup, loads previous session
- **Save State**: After each simulation cycle
- **Preserve Balance**: Ignores config balance if state exists
- **Resume Positions**: Continues monitoring open positions

## Benefits

1. **🛡️ Safety**: No risk of simulation affecting real trades
2. **🔄 Persistence**: Never lose simulation progress
3. **📊 Isolation**: Clean separation of real vs simulated data
4. **⚡ Performance**: Both bots can run without interference
5. **🔍 Debugging**: Separate logs for easier troubleshooting

## File Locations

### Default Structure

```
trading-bot-ai/
├── logs/
│   ├── output_live.log          # Real trading (live)
│   ├── output_testnet.log       # Real trading (testnet)
│   └── output_simulation.log    # Simulation only
└── data/
    ├── active_trades_live.json     # Real positions (live)
    ├── active_trades_testnet.json  # Real positions (testnet)
    └── active_trades_simulation.json # Simulated state
```

All directories are created automatically when needed.

## Testing File Isolation

### Verify Separate Files

```bash
# Run simulation
python simulate_bot.py --once

# Check files created
ls -la logs/ data/

# Should see:
# logs/output_simulation.log
# data/active_trades_simulation.json
```

### Test State Persistence

```bash
# Run simulation with custom balance
SIMULATION_BALANCE=5000 python simulate_bot.py --once

# Run again with different balance
SIMULATION_BALANCE=10000 python simulate_bot.py --once

# Should keep original $5000, not use $10000
```

### Concurrent Execution

```bash
# Start both in different terminals - no conflicts
USE_TESTNET=true python main.py &
python simulate_bot.py &
```

This complete file isolation ensures the simulation bot is a safe, independent environment for testing trading strategies without any risk to real trading operations.
