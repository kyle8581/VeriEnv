#!/bin/bash
# Kill ALL website server processes by port
# Usage: ./kill_all_servers.sh [site_name]

WEBSITES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/websites"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

kill_port() {
    local port="$1"
    if [ -n "$port" ] && [ "$port" -gt 0 ] 2>/dev/null; then
        if fuser "$port/tcp" 2>/dev/null | grep -q .; then
            fuser -k "$port/tcp" 2>/dev/null
            echo -e "  ${RED}killed${NC} port $port"
            return 0
        fi
    fi
    return 1
}

kill_site() {
    local site_name="$1"
    local site_dir="$WEBSITES_DIR/$site_name"
    
    if [ ! -f "$site_dir/ports.json" ]; then
        return 1
    fi
    
    echo -e "${YELLOW}Killing $site_name...${NC}"
    
    ports=$(python3 -c "
import json
try:
    with open('$site_dir/ports.json') as f:
        ports = json.load(f).get('ports', {})
        print(' '.join(str(p) for p in ports.values() if isinstance(p, int)))
except:
    pass
" 2>/dev/null)
    
    killed=0
    for port in $ports; do
        if kill_port "$port"; then
            killed=$((killed + 1))
        fi
    done
    
    if [ $killed -gt 0 ]; then
        echo -e "${GREEN}✓ $site_name - killed $killed processes${NC}"
    fi
}

# Main
if [ -n "$1" ]; then
    kill_site "$1"
else
    echo "=============================================="
    echo "Killing ALL website servers"
    echo "=============================================="
    echo ""
    
    total=0
    for site_dir in "$WEBSITES_DIR"/*/; do
        site_name=$(basename "$site_dir")
        if [ -f "$site_dir/ports.json" ]; then
            kill_site "$site_name"
            total=$((total + 1))
        fi
    done
    
    echo ""
    echo "=============================================="
    echo -e "${GREEN}Done!${NC} Processed $total sites"
    echo "=============================================="
fi















