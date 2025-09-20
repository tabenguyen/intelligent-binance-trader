#!/usr/bin/env python3
"""Quick validation test for simulation bot components."""

import sys
from datetime import datetime
sys.path.insert(0, 'src')

try:
    print('🧪 Testing simulation bot components...')
    
    # Test basic imports
    from src.models.config_models import TradingConfig
    from src.models.trade_models import Trade
    from src.services.notification_service import TwitterNotificationService
    from src.simulated_trading_bot import SimulatedTradingBot, SimulatedPosition
    
    print('✅ All imports successful')
    
    # Test Trade model with enhanced features
    print('Testing Trade model...')
    from src.models.trade_models import TradeDirection, TradeStatus
    trade = Trade(
        id='test_trade_001',
        symbol='BTCUSDT',
        direction=TradeDirection.BUY, 
        quantity=0.001,
        entry_price=50000.0,
        exit_price=None,
        entry_time=datetime.now(),
        exit_time=None,
        status=TradeStatus.PENDING,
        stop_loss=48000.0,
        take_profit=52000.0
    )
    
    print(f'✅ Trade model works: {trade.symbol} {trade.direction.value} quantity={trade.quantity}')
    print(f'   Stop Loss: {trade.stop_loss_percentage:.1f}%')
    print(f'   Take Profit: {trade.take_profit_percentage:.1f}%')
    
    # Test SimulatedPosition
    print('Testing SimulatedPosition...')
    position = SimulatedPosition(
        symbol='BTCUSDT',
        quantity=0.001,
        entry_price=50000.0,
        entry_time=datetime.now(),
        stop_loss=48000.0,
        take_profit=52000.0
    )
    
    print(f'✅ SimulatedPosition works: {position.symbol} quantity={position.quantity} @ ${position.entry_price}')
    
    print('\n🎉 All core components validated successfully!')
    print('🚀 Simulation bot system is ready to use!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)