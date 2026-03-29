#!/usr/bin/env python3
import json
import logging
import socketserver
from pathlib import Path
from typing import Dict, Callable

logger = logging.getLogger("TestMCP")
logging.basicConfig(level=logging.INFO)


class SimpleMCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, mcp_tools, *args, **kwargs):
        self.mcp_tools = mcp_tools
        super().__init__(*args, **kwargs)

    def handle(self):
        try:
            data = self.request.recv(1024).strip()
            if data:
                message = json.loads(data.decode("utf-8"))
                logger.info(f"Received: {message}")

                # Simple echo response for testing
                response = {
                    "status": "success",
                    "message": "MCP Server is working",
                    "received": message,
                }

                self.request.sendall(json.dumps(response).encode("utf-8"))
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            error_response = {"status": "error", "message": str(e)}
            self.request.sendall(json.dumps(error_response).encode("utf-8"))


class SimpleMCPServer:
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.server = None

    def start(self):
        handler = lambda *args, **kwargs: SimpleMCPHandler({}, *args, **kwargs)
        self.server = socketserver.TCPServer((self.host, self.port), handler)
        logger.info(f"MCP Server starting on {self.host}:{self.port}")
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


if __name__ == "__main__":
    server = SimpleMCPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Server")
        server.stop()
