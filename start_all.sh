#!/bin/bash
# AI Employee Vault - Start All Services
# Run: bash start_all.sh

VAULT_DIR="$(cd "$(dirname "$0")" && pwd)"
VAULT_DATA="$VAULT_DIR/vault_data"

echo "========================================"
echo " AI Employee Vault - Starting Services"
echo "========================================"

# Kill existing
kill -9 $(pgrep -f mcp_server_fixed) 2>/dev/null
kill -9 $(pgrep -f mcp_server_social) 2>/dev/null
kill -9 $(pgrep -f orchestrator) 2>/dev/null
kill -9 $(pgrep -f dashboard_server) 2>/dev/null
kill -9 $(pgrep -f playwright-mcp) 2>/dev/null
sleep 1

# Start Core MCP Server (port 8080)
nohup python3 "$VAULT_DIR/src/silver_tier/mcp_server_fixed.py" \
  --vault "$VAULT_DATA" --port 8080 > /tmp/mcp_core.log 2>&1 &
echo "[MCP Core]   PID $! - Port 8080 (17 tools)"

# Start Social MCP Server (port 8081)
nohup python3 "$VAULT_DIR/src/gold_tier/mcp_server_social.py" \
  --vault "$VAULT_DATA" --port 8081 > /tmp/mcp_social.log 2>&1 &
echo "[MCP Social] PID $! - Port 8081 (14 tools)"

# Start Dashboard Server (port 8082)
nohup python3 "$VAULT_DIR/src/dashboard_server.py" > /tmp/dashboard.log 2>&1 &
echo "[Dashboard]   PID $! - Port 8082"

# Start Orchestrator (runs every 5 min)
nohup python3 "$VAULT_DIR/src/orchestrator.py" \
  --vault "$VAULT_DATA" --interval 300 > /tmp/orchestrator.log 2>&1 &
echo "[Orchestrator] PID $! - Interval 300s"

# Start Playwright MCP (port 8808) — browser automation for LinkedIn
nohup npx -y @playwright/mcp@latest --port 8808 --shared-browser-context > /tmp/playwright_mcp.log 2>&1 &
echo "[Playwright] PID $! - Port 8808"

sleep 3

# Verify
echo ""
echo "========================================"
echo " Verification"
echo "========================================"

CORE_OK=$(curl -s http://localhost:8080/status 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK' if d.get('running') else 'FAIL')" 2>/dev/null || echo "FAIL")
SOCIAL_OK=$(curl -s http://localhost:8081/status 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK' if d.get('running') else 'FAIL')" 2>/dev/null || echo "FAIL")
ORCH_OK=$(pgrep -f orchestrator > /dev/null && echo "OK" || echo "FAIL")
DASH_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/api/dashboard 2>/dev/null | grep -q 200 && echo "OK" || echo "FAIL")
PLAYWRIGHT_OK=$(ss -tlnp 2>/dev/null | grep -q 8808 && echo "OK" || echo "FAIL")

echo " MCP Core    : $CORE_OK"
echo " MCP Social  : $SOCIAL_OK"
echo " Orchestrator: $ORCH_OK"
echo " Dashboard   : $DASH_OK"
echo " Playwright  : $PLAYWRIGHT_OK"
echo ""

if [ "$CORE_OK" = "OK" ] && [ "$SOCIAL_OK" = "OK" ] && [ "$ORCH_OK" = "OK" ] && [ "$DASH_OK" = "OK" ]; then
    echo " ✅ All core services running!"
    echo "    Dashboard: http://localhost:8082"
else
    echo " ⚠️ Some services failed - check logs:"
    echo "    tail -20 /tmp/mcp_core.log"
    echo "    tail -20 /tmp/mcp_social.log"
    echo "    tail -20 /tmp/orchestrator.log"
    echo "    tail -20 /tmp/playwright_mcp.log"
fi
