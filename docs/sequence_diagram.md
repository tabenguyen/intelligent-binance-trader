# Trading Bot Workflow - Sequence Diagram

This document contains sequence diagrams explaining the complete workflow of the AI Trading Bot system.

## Main Trading Cycle Flow

```mermaid
sequenceDiagram
    participant User
    participant TradingBot
    participant MarketDataService
    participant TechnicalAnalyzer
    participant EMAStrategy
    participant RiskManager
    participant TradeExecutor
    participant PositionManager
    participant NotificationService

    User->>TradingBot: start()
    TradingBot->>TradingBot: _validate_configuration()

    loop Main Trading Loop (every scan_interval)
        TradingBot->>TradingBot: _trading_cycle()

        Note over TradingBot: Phase 1: Refresh Watchlist
        TradingBot->>TradingBot: _refresh_watchlist()
        TradingBot->>MarketDataService: get_24hr_gainers()
        MarketDataService-->>TradingBot: top_gainers[]

        Note over TradingBot: Phase 2: Update Existing Positions
        TradingBot->>PositionManager: get_positions()
        PositionManager-->>TradingBot: active_positions[]

        alt Has Active Positions
            TradingBot->>TradingBot: _update_positions()
            loop For each position
                TradingBot->>MarketDataService: get_current_price(symbol)
                MarketDataService-->>TradingBot: current_price
                TradingBot->>PositionManager: update_position_price(symbol, price)

                alt No OCO Protection
                    TradingBot->>TradingBot: _place_oco_order(position)
                    TradingBot->>MarketDataService: get_current_price(symbol)
                    MarketDataService-->>TradingBot: current_price
                    TradingBot->>TradeExecutor: execute_oco_order(symbol, quantity, stop_price, limit_price)
                    TradeExecutor-->>TradingBot: OrderResult

                    alt OCO Success
                        TradingBot->>PositionManager: update_oco_order_id(symbol, order_id)
                        TradingBot->>NotificationService: send_oco_notification()
                    else OCO Failed
                        TradingBot->>NotificationService: send_error_notification()
                    end
                end
            end
        end

        Note over TradingBot: Phase 3: Scan for New Opportunities
        TradingBot->>TradingBot: Get symbols without positions

        loop For each symbol to scan
            TradingBot->>MarketDataService: get_market_data(symbol, "4h", 200)
            MarketDataService-->>TradingBot: MarketData

            TradingBot->>TechnicalAnalyzer: calculate_indicators(symbol, klines)
            TechnicalAnalyzer-->>TradingBot: TechnicalAnalysis

            TradingBot->>EMAStrategy: analyze(market_data)
            EMAStrategy-->>TradingBot: TradingSignal (optional)

            alt Signal Generated
                TradingBot->>RiskManager: validate_signal(signal, market_data)
                RiskManager-->>TradingBot: validation_result

                alt Signal Valid
                    TradingBot->>RiskManager: calculate_position_size(signal, account_balance)
                    RiskManager-->>TradingBot: position_size

                    TradingBot->>TradeExecutor: execute_market_buy(symbol, quantity)
                    TradeExecutor-->>TradingBot: OrderResult

                    alt Buy Order Success
                        TradingBot->>PositionManager: create_position(symbol, quantity, entry_price)
                        TradingBot->>NotificationService: send_trade_notification()

                        Note over TradingBot: Immediate OCO Protection
                        TradingBot->>TradingBot: _place_oco_order(position)
                        TradingBot->>TradeExecutor: execute_oco_order(symbol, quantity, stop_price, limit_price)
                        TradeExecutor-->>TradingBot: OrderResult

                        alt OCO Success
                            TradingBot->>PositionManager: update_oco_order_id(symbol, order_id)
                        end
                    else Buy Order Failed
                        TradingBot->>NotificationService: send_error_notification()
                    end
                else Signal Invalid
                    TradingBot->>NotificationService: send_rejection_notification()
                end
            end
        end

        Note over TradingBot: Phase 4: Sleep Until Next Cycle
        TradingBot->>TradingBot: sleep(scan_interval)
    end
```

## OCO Order Creation Workflow

```mermaid
sequenceDiagram
    participant TradingBot
    participant PositionManager
    participant MarketDataService
    participant TradeExecutor
    participant BinanceAPI
    participant NotificationService

    TradingBot->>TradingBot: _place_oco_order(position)

    Note over TradingBot: Step 1: Gather Market Context
    TradingBot->>MarketDataService: get_current_price(symbol)
    MarketDataService->>BinanceAPI: get_ticker_price(symbol)
    BinanceAPI-->>MarketDataService: current_price
    MarketDataService-->>TradingBot: current_price

    Note over TradingBot: Step 2: Validate Balance
    TradingBot->>TradeExecutor: Check balance availability
    TradeExecutor->>BinanceAPI: get_account_info()
    BinanceAPI-->>TradeExecutor: account_balances[]
    TradeExecutor-->>TradingBot: balance_validation_result

    alt Insufficient Balance
        TradingBot->>NotificationService: log_insufficient_balance_error()
        TradingBot-->>TradingBot: return failure
    else Sufficient Balance
        Note over TradingBot: Step 3: Calculate OCO Parameters
        TradingBot->>TradingBot: Calculate stop_loss and take_profit
        TradingBot->>TradingBot: Apply rounding and tolerance

        Note over TradingBot: Step 4: Execute OCO Order
        TradingBot->>TradeExecutor: execute_oco_order(symbol, quantity, stop_price, limit_price)

        Note over TradeExecutor: Balance Validation & Precision Handling
        TradeExecutor->>TradeExecutor: _round_quantity(symbol, quantity)
        TradeExecutor->>TradeExecutor: _round_price(symbol, price)
        TradeExecutor->>TradeExecutor: Apply smart tolerance (0.1%)

        TradeExecutor->>BinanceAPI: new_oco_order(params)
        BinanceAPI-->>TradeExecutor: oco_order_response

        alt OCO Order Success
            TradeExecutor-->>TradingBot: OrderResult(success=True, order_id)
            TradingBot->>PositionManager: update_oco_order_id(symbol, order_id)
            TradingBot->>NotificationService: send_oco_success_notification()
        else OCO Order Failed
            TradeExecutor-->>TradingBot: OrderResult(success=False, error)
            TradingBot->>NotificationService: send_detailed_error_analysis()

            alt Recoverable Error (Insufficient Balance)
                TradingBot->>NotificationService: suggest_balance_aware_script()
            else Non-recoverable Error
                TradingBot->>NotificationService: log_critical_error()
            end
        end
    end
```

## Signal Generation and Validation Workflow

```mermaid
sequenceDiagram
    participant TradingBot
    participant MarketDataService
    participant TechnicalAnalyzer
    participant EMAStrategy
    participant RiskManager
    participant NotificationService

    TradingBot->>MarketDataService: get_market_data(symbol, "4h", 200)
    MarketDataService->>MarketDataService: Fetch klines from Binance
    MarketDataService-->>TradingBot: MarketData(prices, volumes, timestamps)

    TradingBot->>TechnicalAnalyzer: calculate_indicators(symbol, klines)

    Note over TechnicalAnalyzer: Calculate Multiple Indicators
    TechnicalAnalyzer->>TechnicalAnalyzer: calculate_ema(12, 26)
    TechnicalAnalyzer->>TechnicalAnalyzer: calculate_rsi(14)
    TechnicalAnalyzer->>TechnicalAnalyzer: calculate_bollinger_bands()
    TechnicalAnalyzer->>TechnicalAnalyzer: calculate_atr(14)
    TechnicalAnalyzer->>TechnicalAnalyzer: calculate_volume_sma(20)

    TechnicalAnalyzer-->>TradingBot: TechnicalAnalysis(all_indicators)

    TradingBot->>EMAStrategy: analyze(market_data)

    Note over EMAStrategy: Strategy Analysis Process
    EMAStrategy->>EMAStrategy: check_ema_crossover()
    EMAStrategy->>EMAStrategy: validate_rsi_range(45-75)
    EMAStrategy->>EMAStrategy: check_price_above_ema_support()
    EMAStrategy->>EMAStrategy: analyze_daily_trend()
    EMAStrategy->>EMAStrategy: validate_volume_surge()
    EMAStrategy->>EMAStrategy: check_atr_volatility()

    alt Signal Conditions Met
        EMAStrategy->>EMAStrategy: calculate_confidence_score()
        EMAStrategy-->>TradingBot: TradingSignal(BUY, confidence, entry_price)

        TradingBot->>RiskManager: validate_signal(signal, market_data)

        Note over RiskManager: Risk Validation Checks
        RiskManager->>RiskManager: check_market_tradeable()
        RiskManager->>RiskManager: validate_minimum_notional()
        RiskManager->>RiskManager: check_position_concentration()
        RiskManager->>RiskManager: validate_account_balance()

        alt Risk Validation Passed
            RiskManager-->>TradingBot: validation_result(approved=True)

            TradingBot->>RiskManager: calculate_position_size(signal, balance)
            RiskManager->>RiskManager: apply_risk_percentage(2%)
            RiskManager->>RiskManager: respect_minimum_notional(15 USDT)
            RiskManager-->>TradingBot: position_size

            TradingBot->>NotificationService: log_signal_approved()
        else Risk Validation Failed
            RiskManager-->>TradingBot: validation_result(approved=False, reason)
            TradingBot->>NotificationService: log_signal_rejected(reason)
        end
    else No Signal Generated
        EMAStrategy-->>TradingBot: None
        TradingBot->>NotificationService: log_no_signal()
    end
```

## Error Handling and Recovery Workflow

```mermaid
sequenceDiagram
    participant TradingBot
    participant TradeExecutor
    participant BinanceAPI
    participant PositionManager
    participant NotificationService
    participant RecoveryScripts

    TradingBot->>TradeExecutor: execute_oco_order(symbol, quantity, stop_price, limit_price)
    TradeExecutor->>BinanceAPI: new_oco_order(params)
    BinanceAPI-->>TradeExecutor: Error(-2010, "Insufficient balance")

    Note over TradeExecutor: Error Analysis & Logging
    TradeExecutor->>TradeExecutor: analyze_error_code(-2010)
    TradeExecutor->>NotificationService: log_detailed_error_analysis()
    TradeExecutor->>NotificationService: suggest_recovery_actions()

    TradeExecutor-->>TradingBot: OrderResult(success=False, error_code=-2010)

    Note over TradingBot: Automatic Recovery Attempt
    TradingBot->>NotificationService: log_attempting_recovery()

    alt Error Code -2010 (Insufficient Balance)
        TradingBot->>RecoveryScripts: trigger_balance_aware_oco()
        RecoveryScripts->>BinanceAPI: get_account_info()
        BinanceAPI-->>RecoveryScripts: real_time_balances

        RecoveryScripts->>RecoveryScripts: adjust_quantity_to_available_balance()
        RecoveryScripts->>BinanceAPI: new_oco_order(adjusted_params)

        alt Recovery Success
            BinanceAPI-->>RecoveryScripts: oco_order_response
            RecoveryScripts->>PositionManager: update_position_quantity()
            RecoveryScripts->>PositionManager: update_oco_order_id()
            RecoveryScripts->>NotificationService: log_recovery_success()
        else Recovery Failed
            RecoveryScripts->>NotificationService: log_recovery_failure()
            RecoveryScripts->>NotificationService: escalate_to_manual_intervention()
        end

    else Error Code -1013 (Filter Failure)
        TradingBot->>TradeExecutor: retry_with_adjusted_precision()
        TradeExecutor->>TradeExecutor: refetch_symbol_filters()
        TradeExecutor->>TradeExecutor: reapply_precision_rounding()
        TradeExecutor->>BinanceAPI: new_oco_order(corrected_params)

    else Error Code -1102 (Mandatory Parameter Missing)
        TradingBot->>NotificationService: log_configuration_error()
        TradingBot->>NotificationService: request_developer_attention()

    else Other Errors
        TradingBot->>NotificationService: log_unknown_error()
        TradingBot->>NotificationService: schedule_retry_attempt()
    end
```

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[Command Line Interface]
        Scripts[Management Scripts]
    end

    subgraph "Core Trading Bot"
        TB[TradingBot Main]
        Config[TradingConfig]
    end

    subgraph "Strategy Layer"
        BaseStrat[BaseStrategy]
        EMAStrat[EMACrossStrategy]
        CustomStrat[Custom Strategies]
    end

    subgraph "Service Layer"
        MDS[MarketDataService]
        TES[TradeExecutionService]
        RMS[RiskManagementService]
        PMS[PositionManagementService]
        TAS[TechnicalAnalysisService]
        NS[NotificationService]
    end

    subgraph "Core Interfaces"
        IStrat[IStrategy]
        IMDP[IMarketDataProvider]
        ITE[ITradeExecutor]
        IRM[IRiskManager]
        IPM[IPositionManager]
        INS[INotificationService]
        ITA[ITechnicalAnalyzer]
    end

    subgraph "Data Layer"
        ActiveTrades[active_trades.txt]
        Logs[logs/output.log]
        ConfigFile[config/.env]
    end

    subgraph "External APIs"
        BinanceAPI[Binance API]
        MarketData[Market Data Feed]
    end

    CLI --> TB
    Scripts --> TB
    TB --> Config

    TB --> BaseStrat
    BaseStrat --> EMAStrat
    BaseStrat --> CustomStrat

    TB --> MDS
    TB --> TES
    TB --> RMS
    TB --> PMS
    TB --> TAS
    TB --> NS

    MDS -.implements.-> IMDP
    TES -.implements.-> ITE
    RMS -.implements.-> IRM
    PMS -.implements.-> IPM
    TAS -.implements.-> ITA
    NS -.implements.-> INS

    EMAStrat -.implements.-> IStrat
    CustomStrat -.implements.-> IStrat

    PMS --> ActiveTrades
    NS --> Logs
    Config --> ConfigFile

    MDS --> BinanceAPI
    TES --> BinanceAPI
    MDS --> MarketData

    classDef interface fill:#e1f5fe
    classDef service fill:#f3e5f5
    classDef strategy fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef external fill:#ffebee

    class IStrat,IMDP,ITE,IRM,IPM,INS,ITA interface
    class MDS,TES,RMS,PMS,TAS,NS service
    class BaseStrat,EMAStrat,CustomStrat strategy
    class ActiveTrades,Logs,ConfigFile data
    class BinanceAPI,MarketData external
```

## Key Components Description

### 1. TradingBot (Main Orchestrator)

- **Responsibility**: Coordinates all trading activities
- **Key Methods**: `start()`, `_trading_cycle()`, `_update_positions()`, `_place_oco_order()`
- **Dependencies**: All service interfaces via dependency injection

### 2. Strategy Layer

- **EMAStrategy**: Implements EMA crossover with advanced filters
- **BaseStrategy**: Abstract base class for all strategies
- **Signal Generation**: Analyzes market data and generates trading signals

### 3. Service Layer

- **MarketDataService**: Fetches real-time market data from Binance
- **TradeExecutionService**: Executes buy/sell/OCO orders with precision handling
- **RiskManagementService**: Validates signals and calculates position sizes
- **PositionManagementService**: Manages active positions and persistence
- **TechnicalAnalysisService**: Calculates technical indicators
- **NotificationService**: Handles logging and error notifications

### 4. Error Handling & Recovery

- **Smart Balance Validation**: 0.1% tolerance for floating-point precision
- **Automatic OCO Retry**: Balance-aware scripts for recovery
- **Detailed Error Analysis**: Specific handling for different Binance error codes
- **Progressive Recovery**: Multiple fallback strategies for failed operations

### 5. Data Flow

1. **Market Scanning**: Refresh watchlist → Scan symbols → Generate signals
2. **Signal Validation**: Risk checks → Position sizing → Trade execution
3. **Position Management**: Real-time updates → OCO protection → Profit/loss tracking
4. **Error Recovery**: Failed operations → Analysis → Automatic retry → Manual escalation

This architecture follows SOLID principles with clear separation of concerns, dependency injection, and comprehensive error handling for robust trading operations.
