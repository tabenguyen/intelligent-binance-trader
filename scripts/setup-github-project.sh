#!/bin/bash

# GitHub Project Setup Script
# This script helps set up the GitHub Project with all necessary components

set -e

REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-tabenguyen}"
REPO_NAME="${GITHUB_REPOSITORY_NAME:-trading-bot-ai}"
PROJECT_NAME="Trading Bot AI - Development Board"

echo "🚀 Setting up GitHub Project for $REPO_OWNER/$REPO_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed. Please install it first:"
    echo "  - Visit: https://cli.github.com/"
    echo "  - Or run: brew install gh (on macOS)"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    print_error "You are not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

print_status "GitHub CLI is installed and authenticated ✓"

# Create labels if they don't exist
print_status "Creating repository labels..."

# Priority labels
gh label create "priority/critical" --color "d73a4a" --description "Highest priority, immediate attention required" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "priority/high" --color "ff6b35" --description "High priority, should be addressed soon" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "priority/medium" --color "fbca04" --description "Medium priority, normal timeline" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "priority/low" --color "0e8a16" --description "Low priority, can be deferred" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true

# Type labels
gh label create "type/bug" --color "d73a4a" --description "Something isn't working" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "type/feature" --color "a2eeef" --description "New feature or request" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "type/enhancement" --color "84b6eb" --description "Enhancement to existing feature" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "type/documentation" --color "0075ca" --description "Improvements or additions to documentation" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "type/technical-debt" --color "e99695" --description "Technical debt that needs to be addressed" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true

# Component labels
gh label create "component/strategy" --color "5319e7" --description "Trading strategy related" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "component/execution" --color "b60205" --description "Trade execution engine" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "component/risk" --color "ff6b35" --description "Risk management system" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "component/data" --color "0e8a16" --description "Market data and analysis" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "component/monitoring" --color "1d76db" --description "Monitoring and alerting" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "component/infrastructure" --color "0052cc" --description "Infrastructure and deployment" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true

# Status labels
gh label create "status/blocked" --color "d93f0b" --description "Progress is blocked" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "status/in-review" --color "fbca04" --description "Under review" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
gh label create "status/needs-testing" --color "c5def5" --description "Needs testing" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true

print_success "Labels created successfully"

# Create milestones
print_status "Creating initial milestones..."

# Get current date for milestone planning
CURRENT_YEAR=$(date +%Y)
CURRENT_MONTH=$(date +%m)
CURRENT_QUARTER=$(( (CURRENT_MONTH - 1) / 3 + 1 ))

# Create current quarter milestone if it doesn't exist
CURRENT_MILESTONE="Q${CURRENT_QUARTER} ${CURRENT_YEAR} - Core Features"
CURRENT_DUE_DATE=$(date -d "$(( CURRENT_QUARTER * 3 ))/$(( $(date +%d | sed 's/^0//') < 15 ? $(date +%d) : 1 ))/$(( CURRENT_QUARTER == 4 ? CURRENT_YEAR + 1 : CURRENT_YEAR ))" +%Y-%m-%d)

gh api repos/$REPO_OWNER/$REPO_NAME/milestones \
  --method POST \
  --field title="$CURRENT_MILESTONE" \
  --field description="Essential trading bot functionality and stability for Q${CURRENT_QUARTER} ${CURRENT_YEAR}" \
  --field due_on="${CURRENT_DUE_DATE}T23:59:59Z" \
  2>/dev/null || print_warning "Milestone '$CURRENT_MILESTONE' may already exist"

# Create next quarter milestone
NEXT_QUARTER=$(( CURRENT_QUARTER == 4 ? 1 : CURRENT_QUARTER + 1 ))
NEXT_YEAR=$(( CURRENT_QUARTER == 4 ? CURRENT_YEAR + 1 : CURRENT_YEAR ))
NEXT_MILESTONE="Q${NEXT_QUARTER} ${NEXT_YEAR} - Advanced Features"
NEXT_DUE_DATE=$(date -d "${NEXT_QUARTER}/1/${NEXT_YEAR} + 3 months - 1 day" +%Y-%m-%d)

gh api repos/$REPO_OWNER/$REPO_NAME/milestones \
  --method POST \
  --field title="$NEXT_MILESTONE" \
  --field description="Advanced trading strategies and enhanced functionality for Q${NEXT_QUARTER} ${NEXT_YEAR}" \
  --field due_on="${NEXT_DUE_DATE}T23:59:59Z" \
  2>/dev/null || print_warning "Milestone '$NEXT_MILESTONE' may already exist"

print_success "Milestones created successfully"

# Create initial issues for project setup
print_status "Creating initial project issues..."

# Create a sample feature issue
gh issue create \
  --title "Implement Advanced Risk Management System" \
  --body "## 📋 Feature Description

Implement an advanced risk management system with the following capabilities:

### Requirements
- [ ] Portfolio-level risk limits
- [ ] Dynamic position sizing based on volatility
- [ ] Correlation analysis between positions
- [ ] Real-time risk monitoring dashboard

### Acceptance Criteria
- [ ] Risk limits are enforced across all trades
- [ ] Position sizes adjust based on market volatility
- [ ] System prevents correlated positions from exceeding limits
- [ ] Dashboard shows real-time risk metrics

### Technical Notes
- Integrate with existing risk management service
- Consider using VaR (Value at Risk) calculations
- Implement circuit breakers for extreme market conditions

### Definition of Done
- [ ] Code implemented and tested
- [ ] Documentation updated
- [ ] Integration tests pass
- [ ] Performance benchmarks met" \
  --label "type/feature,component/risk,priority/high" \
  --milestone "$CURRENT_MILESTONE" \
  --repo "$REPO_OWNER/$REPO_NAME" \
  2>/dev/null || print_warning "Sample feature issue may already exist"

# Create a sample bug issue
gh issue create \
  --title "Order Status Check Failing for Non-Existent Orders" \
  --body "## 🐛 Bug Description

The trading bot continuously tries to check the status of OCO orders that no longer exist, causing log spam and potential performance issues.

### Steps to Reproduce
1. Place an OCO order
2. Order gets executed or cancelled externally
3. Bot continues to check order status
4. Receives 'Order does not exist' errors repeatedly

### Expected Behavior
- Bot should detect when orders no longer exist
- Remove stale order references from position tracking
- Stop attempting to check non-existent orders

### Actual Behavior
- Continuous API calls to check non-existent orders
- Log spam with error messages
- Potential rate limiting issues

### Error Messages
\`\`\`
Could not get status for order 13636395733 on PUNDIXUSDT: (400, -2013, 'Order does not exist.')
\`\`\`

### Environment
- Mode: Testnet
- Version: Current develop branch

### Proposed Solution
- Add order existence validation
- Implement cleanup mechanism for stale orders
- Add error handling for -2013 error codes" \
  --label "type/bug,component/execution,priority/critical" \
  --milestone "$CURRENT_MILESTONE" \
  --repo "$REPO_OWNER/$REPO_NAME" \
  2>/dev/null || print_warning "Sample bug issue may already exist"

print_success "Initial issues created successfully"

# Instructions for creating the GitHub Project
print_status "GitHub Project Setup Instructions:"
echo ""
echo "To complete the setup, you need to create a GitHub Project (Beta) manually:"
echo ""
echo "1. Go to: https://github.com/$REPO_OWNER/$REPO_NAME/projects"
echo "2. Click 'New project'"
echo "3. Choose 'Board' template"
echo "4. Name it: '$PROJECT_NAME'"
echo "5. Add the following custom fields:"
echo "   - Story Points (Single select): 1, 2, 3, 5, 8, 13, 21"
echo "   - Technical Complexity (Single select): Low, Medium, High, Expert"
echo "   - Business Value (Single select): Low, Medium, High, Critical"
echo "   - Risk Level (Single select): Low, Medium, High, Critical"
echo ""
echo "6. Set up automation rules in the project settings:"
echo "   - Auto-add items with specific labels"
echo "   - Move items to 'In Progress' when assigned"
echo "   - Move items to 'Done' when PR is merged"
echo ""

print_success "GitHub Project setup script completed!"
print_status "Don't forget to:"
echo "  ✓ Create the GitHub Project manually (see instructions above)"
echo "  ✓ Configure project automation rules"
echo "  ✓ Add team members to the repository"
echo "  ✓ Review and customize issue templates in .github/ISSUE_TEMPLATE/"
echo "  ✓ Enable branch protection rules"
echo ""
print_success "Your repository is now ready for project management! 🎉"
