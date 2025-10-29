#!/bin/bash
# =============================================================================
# Cleanup Script for Smart TV Digital Signage Project
# =============================================================================
# Removes temporary and cache files from the codebase
#
# Usage:
#   ./scripts/cleanup.sh           # Run cleanup
#   ./scripts/cleanup.sh --dry-run # Preview what will be deleted
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if dry-run mode
DRY_RUN=false
if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
    echo -e "${YELLOW}DRY RUN MODE - No files will be deleted${NC}"
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}Starting cleanup for: $PROJECT_ROOT${NC}"

# Function to delete or preview files
cleanup_files() {
    local pattern=$1
    local description=$2

    echo -e "\n${YELLOW}Cleaning: $description${NC}"

    if [ "$DRY_RUN" = true ]; then
        find "$PROJECT_ROOT" -name "$pattern" -type f 2>/dev/null | while read -r file; do
            echo "  Would delete: $file"
        done
    else
        local count=0
        find "$PROJECT_ROOT" -name "$pattern" -type f 2>/dev/null | while read -r file; do
            rm -f "$file"
            count=$((count + 1))
            echo "  Deleted: $file"
        done
        if [ $count -eq 0 ]; then
            echo "  No files found"
        fi
    fi
}

# Function to delete or preview directories
cleanup_dirs() {
    local dirname=$1
    local description=$2

    echo -e "\n${YELLOW}Cleaning: $description${NC}"

    if [ "$DRY_RUN" = true ]; then
        find "$PROJECT_ROOT" -name "$dirname" -type d 2>/dev/null | while read -r dir; do
            echo "  Would delete: $dir"
        done
    else
        local count=0
        find "$PROJECT_ROOT" -name "$dirname" -type d 2>/dev/null | while read -r dir; do
            rm -rf "$dir"
            count=$((count + 1))
            echo "  Deleted: $dir"
        done
        if [ $count -eq 0 ]; then
            echo "  No directories found"
        fi
    fi
}

# Start cleanup
echo -e "\n${GREEN}=== CLEANUP STARTED ===${NC}"

# Python cache files
cleanup_dirs "__pycache__" "Python cache directories"
cleanup_files "*.pyc" "Python compiled files (.pyc)"
cleanup_files "*.pyo" "Python optimized files (.pyo)"
cleanup_files "*.pyd" "Python dynamic libraries (.pyd)"

# Backup files
cleanup_files "*.bak" "Backup files (.bak)"
cleanup_files "*.old" "Old files (.old)"
cleanup_files "*.orig" "Original files (.orig)"
cleanup_files "*~" "Editor backup files (~)"

# Temporary files
cleanup_files "*.tmp" "Temporary files (.tmp)"
cleanup_files ".*.swp" "Vim swap files (.swp)"
cleanup_files ".*.swo" "Vim swap files (.swo)"

# OS-specific files
cleanup_files ".DS_Store" "macOS metadata files"
cleanup_files "Thumbs.db" "Windows thumbnail cache"
cleanup_files "desktop.ini" "Windows folder config"

# Log files (except in logs directory)
find "$PROJECT_ROOT" -name "*.log" -not -path "*/logs/*" -type f 2>/dev/null | while read -r file; do
    if [ "$DRY_RUN" = true ]; then
        echo "  Would delete: $file"
    else
        rm -f "$file"
        echo "  Deleted: $file"
    fi
done

# Node.js (if applicable)
if [ -d "$PROJECT_ROOT/node_modules" ]; then
    echo -e "\n${YELLOW}Note: node_modules found but not deleted (use npm clean instead)${NC}"
fi

# Calculate space saved (approximate)
if [ "$DRY_RUN" = false ]; then
    echo -e "\n${GREEN}=== CLEANUP COMPLETED ===${NC}"
    echo -e "${GREEN}Temporary and cache files have been removed${NC}"
else
    echo -e "\n${YELLOW}=== DRY RUN COMPLETED ===${NC}"
    echo -e "${YELLOW}Run without --dry-run to actually delete files${NC}"
fi

# Recommendations
echo -e "\n${GREEN}Recommendations:${NC}"
echo "  - Run this script periodically to maintain clean codebase"
echo "  - Use 'git status' to ensure no needed files were deleted"
echo "  - Python cache will regenerate automatically on next run"
