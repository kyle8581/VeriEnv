#!/bin/bash
# Check status of all website servers
# Usage: ./check_servers.sh [--only-down]

WEBSITES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/websites"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ONLY_DOWN=false
if [ "$1" == "--only-down" ]; then
    ONLY_DOWN=true
fi

echo "=============================================="
echo "Website Server Status Check"
echo "=============================================="
echo ""

total=0
up=0
down=0

# Find all sites with ports.json and task_instructions.json
for ports_file in $(find "$WEBSITES_DIR" -maxdepth 2 -name "ports.json" 2>/dev/null); do
    site_dir=$(dirname "$ports_file")
    site_name=$(basename "$site_dir")
    
    # Check if has tasks
    if [ ! -f "$site_dir/task_instructions.json" ]; then
        continue
    fi
    
    total=$((total + 1))
    
    # Get frontend port
    port=$(python3 -c "
import json
with open('$ports_file') as f:
    ports = json.load(f).get('ports', {})
    print(ports.get('FRONTEND_PORT') or ports.get('WEB_PORT') or ports.get('PORT') or '')
" 2>/dev/null)
    
    if [ -z "$port" ]; then
        if [ "$ONLY_DOWN" = false ]; then
            echo -e "${YELLOW}? $site_name - No port found${NC}"
        fi
        continue
    fi
    
    # Check if port is responding
    status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://localhost:$port" 2>/dev/null)
    
    if [ "$status" == "200" ] || [ "$status" == "304" ] || [ "$status" == "301" ] || [ "$status" == "302" ]; then
        up=$((up + 1))
        if [ "$ONLY_DOWN" = false ]; then
            echo -e "${GREEN}✓ $site_name${NC} (port $port) - $status"
        fi
    else
        down=$((down + 1))
        echo -e "${RED}✗ $site_name${NC} (port $port) - $status"
    fi
done

echo ""
echo "=============================================="
echo -e "Total: $total | ${GREEN}Up: $up${NC} | ${RED}Down: $down${NC}"
echo "=============================================="















