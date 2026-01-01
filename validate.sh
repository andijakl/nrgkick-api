#!/bin/bash
# validate.sh - Validate the nrgkick-api library before committing/releasing
#
# This script:
# 1. Ensures the virtual environment is activated
# 2. Updates pre-commit hooks to latest versions
# 3. Runs all pre-commit hooks
# 4. Checks if files were modified and need git staging
# 5. Runs all tests with coverage
#
# Usage: ./validate.sh [--no-update] [--no-tests]
#   --no-update  Skip updating pre-commit hooks
#   --no-tests   Skip running tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
UPDATE_HOOKS=true
RUN_TESTS=true
for arg in "$@"; do
    case $arg in
        --no-update)
            UPDATE_HOOKS=false
            shift
            ;;
        --no-tests)
            RUN_TESTS=false
            shift
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  NRGkick API Library Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get script directory (works even if called from another directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Check/activate virtual environment
echo -e "${YELLOW}Step 1: Checking virtual environment...${NC}"

if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -f "venv/bin/activate" ]]; then
        echo "  Activating virtual environment..."
        source venv/bin/activate
        echo -e "  ${GREEN}✓ Virtual environment activated${NC}"
    elif [[ -f "venv/Scripts/activate" ]]; then
        # Windows Git Bash
        echo "  Activating virtual environment (Windows)..."
        source venv/Scripts/activate
        echo -e "  ${GREEN}✓ Virtual environment activated${NC}"
    else
        echo -e "  ${RED}✗ No virtual environment found!${NC}"
        echo "  Please create one first: python -m venv venv"
        echo "  Then activate it: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows)"
        echo "  Next, install requirements with: pip install -e .[dev]"
        exit 1
    fi
else
    echo -e "  ${GREEN}✓ Virtual environment already active: $VIRTUAL_ENV${NC}"
fi

# Step 2: Ensure pre-commit is installed
echo ""
echo -e "${YELLOW}Step 2: Checking pre-commit installation...${NC}"

if ! command -v pre-commit &> /dev/null; then
    echo "  Installing pre-commit..."
    pip install pre-commit
fi
echo -e "  ${GREEN}✓ pre-commit is installed${NC}"

# Step 3: Update pre-commit hooks (optional)
echo ""
echo -e "${YELLOW}Step 3: Pre-commit hooks...${NC}"

if [[ "$UPDATE_HOOKS" == true ]]; then
    echo "  Updating hooks to latest versions..."
    pre-commit autoupdate
    echo -e "  ${GREEN}✓ Hooks updated${NC}"
else
    echo -e "  ${BLUE}ℹ Skipping hook updates (--no-update)${NC}"
fi

# Step 4: Run pre-commit hooks
echo ""
echo -e "${YELLOW}Step 4: Running pre-commit hooks...${NC}"

# Capture modified files before running hooks
MODIFIED_BEFORE=$(git status --porcelain 2>/dev/null || echo "")

# Run pre-commit (don't exit on failure, we want to check for modifications)
set +e
pre-commit run --all-files
PRECOMMIT_EXIT=$?
set -e

# Step 5: Check if files were modified
echo ""
echo -e "${YELLOW}Step 5: Checking for modified files...${NC}"

MODIFIED_AFTER=$(git status --porcelain 2>/dev/null || echo "")

if [[ "$MODIFIED_BEFORE" != "$MODIFIED_AFTER" ]]; then
    echo -e "  ${YELLOW}⚠ Pre-commit hooks modified some files:${NC}"
    git status --short
    echo ""
    echo -e "  ${YELLOW}Please review the changes and stage them with:${NC}"
    echo -e "    git add -A"
    echo ""
    NEEDS_STAGING=true
else
    echo -e "  ${GREEN}✓ No files were modified by hooks${NC}"
    NEEDS_STAGING=false
fi

# Check pre-commit result
if [[ $PRECOMMIT_EXIT -ne 0 ]]; then
    echo ""
    echo -e "${RED}✗ Pre-commit hooks failed!${NC}"
    echo "  Please fix the issues above and run validate.sh again."
    exit 1
fi

echo -e "  ${GREEN}✓ All pre-commit hooks passed${NC}"

# Step 6: Run tests (optional)
echo ""
echo -e "${YELLOW}Step 6: Running tests...${NC}"

if [[ "$RUN_TESTS" == true ]]; then
    pytest tests/ -v --cov=src/nrgkick_api --cov-report=term-missing
    echo -e "  ${GREEN}✓ All tests passed${NC}"
else
    echo -e "  ${BLUE}ℹ Skipping tests (--no-tests)${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  Validation Complete!${NC}"
echo -e "${BLUE}========================================${NC}"

if [[ "$NEEDS_STAGING" == true ]]; then
    echo ""
    echo -e "${YELLOW}Note: Some files were modified by pre-commit hooks.${NC}"
    echo "Run 'git add -A' to stage the changes before committing."
fi

echo ""
echo "Next steps:"
echo "  1. git add -A"
echo "  2. git commit -m 'Your message'"
echo "  3. git push"
echo ""
