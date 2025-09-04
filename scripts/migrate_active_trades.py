#!/usr/bin/env python3
"""
Script to migrate existing active_trades.txt to include oco_order_id field.
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig

def migrate_active_trades():
    """Migrate active trades file to include oco_order_id field."""
    load_environment()
    config = TradingConfig.from_env()
    
    trades_file = config.active_trades_file
    
    print(f"Migrating active trades file: {trades_file}")
    
    if not os.path.exists(trades_file):
        print("No active trades file found - nothing to migrate.")
        return
    
    # Create backup
    backup_file = f"{trades_file}.backup"
    
    try:
        # Read current data
        with open(trades_file, 'r') as f:
            data = json.load(f)
        
        print(f"Found {len(data)} positions to migrate")
        
        # Create backup
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Created backup: {backup_file}")
        
        # Migrate data - add oco_order_id field
        migrated_count = 0
        for symbol, position_data in data.items():
            if 'oco_order_id' not in position_data:
                position_data['oco_order_id'] = None  # Legacy positions have no OCO order ID
                migrated_count += 1
                print(f"  Migrated {symbol}: added oco_order_id field")
        
        # Save migrated data
        if migrated_count > 0:
            with open(trades_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Migration complete: {migrated_count} positions updated")
        else:
            print("✅ No migration needed - all positions already have oco_order_id field")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        
        # Restore backup if something went wrong
        if os.path.exists(backup_file):
            print("Restoring from backup...")
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            with open(trades_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            print("Backup restored successfully")

if __name__ == "__main__":
    migrate_active_trades()
