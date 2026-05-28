#!/bin/bash
# AI Employee Vault - Stop All Services
echo "Stopping AI Employee Vault services..."
kill -9 $(pgrep -f mcp_server_fixed) 2>/dev/null
kill -9 $(pgrep -f mcp_server_social) 2>/dev/null
kill -9 $(pgrep -f orchestrator) 2>/dev/null
kill -9 $(pgrep -f dashboard_server) 2>/dev/null
kill -9 $(pgrep -f playwright-mcp) 2>/dev/null
sleep 1
echo "All services stopped."
