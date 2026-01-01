#!/bin/bash

################################################################################
# Health Check Script untuk Nomad Stack
# Usage: ./health-check.sh
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "════════════════════════════════════════════════════════"
echo "       Nomad Stack Health Check"
echo "════════════════════════════════════════════════════════"
echo ""

# Check Docker
echo -n "Docker Service: "
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✓ RUNNING${NC}"
    docker --version
else
    echo -e "${RED}✗ NOT RUNNING${NC}"
fi
echo ""

# Check Nomad
echo -n "Nomad Service: "
if systemctl is-active --quiet nomad; then
    echo -e "${GREEN}✓ RUNNING${NC}"
    nomad version | head -1
    echo ""
    echo "Nomad Server Members:"
    nomad server members
    echo ""
    echo "Nomad Nodes:"
    nomad node status
else
    echo -e "${RED}✗ NOT RUNNING${NC}"
fi
echo ""

# Check Consul
echo -n "Consul Service: "
if systemctl is-active --quiet consul; then
    echo -e "${GREEN}✓ RUNNING${NC}"
    consul version | head -1
    echo ""
    echo "Consul Members:"
    consul members
    echo ""
    echo "Consul Services:"
    consul catalog services
else
    echo -e "${RED}✗ NOT RUNNING${NC}"
fi
echo ""

# Check Nomad Jobs
echo "Running Jobs:"
nomad job status 2>/dev/null || echo "  No jobs running"
echo ""

# Check Docker Containers
echo "Running Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  No containers running"
echo ""

# Check System Resources
echo "System Resources:"
echo "  CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
echo "  Memory: $(free -h | awk 'NR==2{printf "%s / %s (%.2f%%)", $3, $2, $3*100/$2}')"
echo "  Disk: $(df -h / | awk 'NR==2{printf "%s / %s (%s)", $3, $2, $5}')"
echo ""

# Check Listening Ports
echo "Listening Ports:"
ss -tulpn | grep -E "4646|4647|4648|8500|8300|2375|2376" | awk '{print "  "$5}' | sort -u
echo ""

# Web UIs
PUBLIC_IP=$(hostname -I | awk '{print $1}')
echo "Web UIs:"
echo "  - Nomad:  http://${PUBLIC_IP}:4646"
echo "  - Consul: http://${PUBLIC_IP}:8500"
echo ""

echo "════════════════════════════════════════════════════════"
echo "Health Check Complete!"
echo "════════════════════════════════════════════════════════"
