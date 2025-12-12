#!/bin/bash
# create_release.sh - Create a release package for nrgkick-api
#
# This script:
# 1. Updates the version in pyproject.toml (if specified)
# 2. Runs full validation (pre-commit + tests)
# 3. Builds the distribution package
# 4. Runs twine check on the package
# 5. Provides instructions for publishing
#
# Usage: ./create_release.sh [VERSION]
#   VERSION  New version number (e.g., 1.0.1, 1.1.0, 2.0.0)
#            If not specified, uses current version from pyproject.toml
#
# Examples:
#   ./create_release.sh           # Build with current version
#   ./create_release.sh 1.0.1     # Update to 1.0.1 and build
#   ./create_release.sh 1.1.0     # Update to 1.1.0 and build

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  NRGkick API Release Builder${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check/activate virtual environment
echo -e "${YELLOW}Checking virtual environment...${NC}"

if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    elif [[ -f "venv/Scripts/activate" ]]; then
        source venv/Scripts/activate
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    else
        echo -e "${RED}✗ No virtual environment found!${NC}"
        echo "Please create one first: python -m venv venv && pip install -e '.[dev]'"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Virtual environment already active${NC}"
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep -E '^version\s*=' pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/')
echo -e "Current version: ${CYAN}${CURRENT_VERSION}${NC}"

# Step 1: Update version if specified
NEW_VERSION="${1:-$CURRENT_VERSION}"

if [[ "$NEW_VERSION" != "$CURRENT_VERSION" ]]; then
    echo ""
    echo -e "${YELLOW}Step 1: Updating version to ${NEW_VERSION}...${NC}"
    
    # Validate version format (basic semver check)
    if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo -e "${RED}✗ Invalid version format: $NEW_VERSION${NC}"
        echo "  Please use semantic versioning (e.g., 1.0.1, 1.1.0, 2.0.0)"
        exit 1
    fi
    
    # Update version in pyproject.toml
    sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
    
    echo -e "${GREEN}✓ Version updated to ${NEW_VERSION}${NC}"
    VERSION_CHANGED=true
else
    echo ""
    echo -e "${YELLOW}Step 1: Using current version ${CURRENT_VERSION}${NC}"
    VERSION_CHANGED=false
fi

# Step 2: Run validation
echo ""
echo -e "${YELLOW}Step 2: Running validation...${NC}"
echo ""

# Run validate.sh without hook updates (we want deterministic builds)
./validate.sh --no-update

# Step 3: Clean previous builds
echo ""
echo -e "${YELLOW}Step 3: Cleaning previous builds...${NC}"

rm -rf dist/ build/ src/*.egg-info
echo -e "${GREEN}✓ Build directories cleaned${NC}"

# Step 4: Build the package
echo ""
echo -e "${YELLOW}Step 4: Building distribution package...${NC}"

python -m build

echo -e "${GREEN}✓ Package built successfully${NC}"

# Step 5: Check the package
echo ""
echo -e "${YELLOW}Step 5: Validating package with twine...${NC}"

twine check dist/*

echo -e "${GREEN}✓ Package validation passed${NC}"

# Step 6: Show package contents
echo ""
echo -e "${YELLOW}Step 6: Package contents:${NC}"
ls -la dist/

# Calculate package sizes
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
TARBALL_FILE=$(ls dist/*.tar.gz 2>/dev/null | head -1)

if [[ -f "$WHEEL_FILE" ]]; then
    WHEEL_SIZE=$(du -h "$WHEEL_FILE" | cut -f1)
    echo -e "  Wheel:   ${CYAN}$(basename "$WHEEL_FILE")${NC} ($WHEEL_SIZE)"
fi
if [[ -f "$TARBALL_FILE" ]]; then
    TAR_SIZE=$(du -h "$TARBALL_FILE" | cut -f1)
    echo -e "  Tarball: ${CYAN}$(basename "$TARBALL_FILE")${NC} ($TAR_SIZE)"
fi

# Summary and next steps
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  Release Package Ready!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Version: ${CYAN}${NEW_VERSION}${NC}"
echo ""

if [[ "$VERSION_CHANGED" == true ]]; then
    echo -e "${YELLOW}Files were modified. Complete these steps to publish:${NC}"
    echo ""
    echo "1. Review and commit the version change:"
    echo -e "   ${CYAN}git add pyproject.toml${NC}"
    echo -e "   ${CYAN}git commit -m \"Bump version to ${NEW_VERSION}\"${NC}"
    echo ""
else
    echo -e "${YELLOW}Complete these steps to publish:${NC}"
    echo ""
    echo "1. Ensure all changes are committed:"
    echo -e "   ${CYAN}git status${NC}"
    echo ""
fi

echo "2. Create and push a version tag:"
echo -e "   ${CYAN}git tag -a v${NEW_VERSION} -m \"Release v${NEW_VERSION}\"${NC}"
echo -e "   ${CYAN}git push origin main${NC}"
echo -e "   ${CYAN}git push origin v${NEW_VERSION}${NC}"
echo ""
echo "3. Create a GitHub release:"
echo -e "   ${CYAN}https://github.com/andijakl/nrgkick-api/releases/new${NC}"
echo "   - Select tag: v${NEW_VERSION}"
echo "   - Title: v${NEW_VERSION}"
echo "   - This will trigger automatic PyPI publishing via GitHub Actions"
echo ""
echo "4. (Alternative) Manual upload to PyPI:"
echo -e "   ${CYAN}twine upload dist/*${NC}"
echo "   Username: __token__"
echo "   Password: <your PyPI API token>"
echo ""
echo "5. Verify on PyPI:"
echo -e "   ${CYAN}https://pypi.org/project/nrgkick-api/${NEW_VERSION}/${NC}"
echo ""
echo "6. Test installation:"
echo -e "   ${CYAN}pip install nrgkick-api==${NEW_VERSION}${NC}"
echo ""

# Remind about CHANGELOG
if [[ -f "CHANGELOG.md" ]]; then
    echo -e "${YELLOW}Don't forget to update CHANGELOG.md!${NC}"
    echo ""
fi
