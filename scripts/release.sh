#!/bin/bash
# Release script for rez-proxy using GoReleaser

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if version is provided
if [ $# -eq 0 ]; then
    log_error "Please provide a version number"
    echo "Usage: $0 <version> [--dry-run] [--snapshot]"
    echo "Example: $0 1.0.0"
    exit 1
fi

VERSION=$1
DRY_RUN=false
SNAPSHOT=false

# Parse additional arguments
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --snapshot)
            SNAPSHOT=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info "Starting release process for version $VERSION"

# Check prerequisites
log_info "Checking prerequisites..."

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    log_warning "Not on main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    log_error "Working directory is not clean"
    git status --short
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    log_error "uv is not installed"
    exit 1
fi

# Check if goreleaser is available
if ! command -v goreleaser &> /dev/null; then
    log_error "goreleaser is not installed"
    echo "Install it with: go install github.com/goreleaser/goreleaser/v2@latest"
    exit 1
fi

log_success "Prerequisites check passed"

# Update version in pyproject.toml
log_info "Updating version in pyproject.toml to $VERSION"
sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Commit version change
if [ "$DRY_RUN" = false ]; then
    git add pyproject.toml
    git commit -m "chore: bump version to $VERSION"
    log_success "Version updated and committed"
fi

# Create and push tag
if [ "$DRY_RUN" = false ] && [ "$SNAPSHOT" = false ]; then
    log_info "Creating and pushing tag v$VERSION"
    git tag "v$VERSION"
    git push origin "v$VERSION"
    log_success "Tag created and pushed"
fi

# Run GoReleaser
log_info "Running GoReleaser..."

if [ "$DRY_RUN" = true ]; then
    goreleaser release --snapshot --clean --skip=publish
    log_success "Dry run completed successfully"
elif [ "$SNAPSHOT" = true ]; then
    goreleaser release --snapshot --clean --skip=publish
    log_success "Snapshot build completed successfully"
else
    goreleaser release --clean
    log_success "Release completed successfully"
fi

log_success "🎉 Release process completed!"

if [ "$DRY_RUN" = false ] && [ "$SNAPSHOT" = false ]; then
    log_info "Package should be available at:"
    echo "  📦 PyPI: https://pypi.org/project/rez-proxy/$VERSION/"
    echo "  🐙 GitHub: https://github.com/loonghao/rez-proxy/releases/tag/v$VERSION"
fi
