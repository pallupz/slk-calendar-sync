#!/bin/bash

# SLK Calendar Sync Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏆 Super League Kerala Calendar Sync${NC}"
echo "=================================="

# Run the sync
echo -e "${GREEN}🚀 Starting sync...${NC}"
/usr/local/bin/uv run slk_sync.py "$@"

echo -e "${GREEN}✅ Sync completed!${NC}"
