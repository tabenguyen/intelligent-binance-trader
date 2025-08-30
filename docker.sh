#!/bin/bash

# Docker management script for Coin Gemini Trading Bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        log_warning ".env file not found"
        if [ -f .env.docker ]; then
            log_info "Copying .env.docker to .env"
            cp .env.docker .env
            log_warning "Please edit .env file with your actual API keys before starting the bot"
        else
            log_error "No environment file found. Please create .env file with your API keys"
            exit 1
        fi
    fi
}

# Create required directories
setup_dirs() {
    log_info "Creating required directories..."
    mkdir -p data logs
    log_success "Directories created"
}

# Build the Docker image
build() {
    log_info "Building Docker image..."
    docker-compose build
    log_success "Docker image built successfully"
}

# Start the trading bot
start() {
    check_env
    setup_dirs
    log_info "Starting Coin Gemini Trading Bot..."
    docker-compose up -d
    log_success "Trading bot started successfully"
    log_info "Use 'docker-compose logs -f' to view logs"
}

# Stop the trading bot
stop() {
    log_info "Stopping Coin Gemini Trading Bot..."
    docker-compose down
    log_success "Trading bot stopped successfully"
}

# Restart the trading bot
restart() {
    log_info "Restarting Coin Gemini Trading Bot..."
    docker-compose restart
    log_success "Trading bot restarted successfully"
}

# View logs
logs() {
    log_info "Showing trading bot logs..."
    docker-compose logs -f trading-bot
}

# Show status
status() {
    log_info "Trading bot status:"
    docker-compose ps
}

# Update and restart
update() {
    log_info "Updating and restarting trading bot..."
    docker-compose down
    docker-compose build
    docker-compose up -d
    log_success "Trading bot updated and restarted"
}

# Clean up
clean() {
    log_warning "This will remove all containers, images, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Show help
help() {
    echo "Coin Gemini Trading Bot Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build    Build the Docker image"
    echo "  start    Start the trading bot"
    echo "  stop     Stop the trading bot"
    echo "  restart  Restart the trading bot"
    echo "  logs     View trading bot logs"
    echo "  status   Show trading bot status"
    echo "  update   Update and restart the bot"
    echo "  clean    Remove all Docker resources"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start the trading bot"
    echo "  $0 logs      # View logs in real-time"
    echo "  $0 status    # Check if bot is running"
}

# Main script logic
case "${1:-}" in
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    update)
        update
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        help
        ;;
    *)
        log_error "Unknown command: ${1:-}"
        echo ""
        help
        exit 1
        ;;
esac
