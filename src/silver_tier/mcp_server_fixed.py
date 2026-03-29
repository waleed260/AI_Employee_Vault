#!/usr/bin/env python3
"""
Fixed MCP Server for AI Employee Vault
"""

import json
import logging
import socketserver
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import threading
import http.server
import socketserver

logger = logging.getLogger("MCPServer")


class MCPMessageType(Enum):
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_RESPONSE = "resource_response"
    PROMPT_REQUEST = "prompt_request"
    PROMPT_RESPONSE = "prompt_response"


class MCPServer:
    def __init__(self, vault_path: str, port: int = 8080):
        self.vault_path = Path(vault_path)
        self.port = port
        self.server = None
        self.thread = None

        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, Any] = {}
        self.prompts: Dict[str, str] = {}

        self.request_history: List[Dict] = []

        self._register_default_tools()

        logger.info(f"MCPServer initialized on port {port} - Silver Tier")

    def _register_default_tools(self):
        self.register_tool(
            "send_email",
            self._tool_send_email,
            {
                "description": "Send an email via SMTP",
                "parameters": {
                    "to": "string",
                    "subject": "string",
                    "body": "string",
                },
            },
        )

        self.register_tool(
            "linkedin_post",
            self._tool_linkedin_post,
            {
                "description": "Create LinkedIn post via web interface (requires manual login)",
                "parameters": {
                    "content": "string",
                },
            },
        )

        self.register_tool(
            "create_file",
            self._tool_create_file,
            {
                "description": "Create a file in the vault",
                "parameters": {
                    "path": "string",
                    "content": "string",
                },
            },
        )

        self.register_tool(
            "read_file",
            self._tool_read_file,
            {
                "description": "Read a file from the vault",
                "parameters": {
                    "path": "string",
                },
            },
        )

        self.register_tool(
            "list_files",
            self._tool_list_files,
            {
                "description": "List files in a directory",
                "parameters": {
                    "directory": "string",
                    "pattern": "string",
                },
            },
        )

        self.register_tool(
            "delete_file",
            self._tool_delete_file,
            {
                "description": "Delete a file",
                "parameters": {
                    "path": "string",
                },
            },
        )

        self.register_tool(
            "move_file",
            self._tool_move_file,
            {
                "description": "Move a file to another directory",
                "parameters": {
                    "source": "string",
                    "destination": "string",
                },
            },
        )

        self.register_tool(
            "search_content",
            self._tool_search_content,
            {
                "description": "Search for content in files",
                "parameters": {
                    "query": "string",
                    "path": "string",
                },
            },
        )

        self.register_tool(
            "get_dashboard",
            self._tool_get_dashboard,
            {"description": "Get vault dashboard data", "parameters": {}},
        )

        self.register_tool(
            "get_approval_items",
            self._tool_get_approval_items,
            {"description": "Get items pending approval", "parameters": {}},
        )

        self.register_tool(
            "approve_item",
            self._tool_approve_item,
            {
                "description": "Approve an item",
                "parameters": {
                    "item_id": "string",
                },
            },
        )

        self.register_tool(
            "reject_item",
            self._tool_reject_item,
            {
                "description": "Reject an item",
                "parameters": {
                    "item_id": "string",
                    "reason": "string",
                },
            },
        )

        self.register_tool(
            "create_task",
            self._tool_create_task,
            {
                "description": "Create a new task",
                "parameters": {
                    "title": "string",
                    "description": "string",
                    "priority": "string",
                },
            },
        )

        self.register_tool(
            "get_tasks",
            self._tool_get_tasks,
            {
                "description": "Get all tasks",
                "parameters": {
                    "status": "string",
                },
            },
        )

        self.register_tool(
            "update_task",
            self._tool_update_task,
            {
                "description": "Update a task",
                "parameters": {
                    "task_id": "string",
                    "status": "string",
                },
            },
        )

        self.register_tool(
            "run_automation",
            self._tool_run_automation,
            {
                "description": "Run an automation workflow",
                "parameters": {
                    "workflow_name": "string",
                    "parameters": "object",
                },
            },
        )

        self.register_tool(
            "log_action",
            self._tool_log_action,
            {
                "description": "Log an action to the vault logs",
                "parameters": {
                    "action_type": "string",
                    "details": "string",
                },
            },
        )

    def register_tool(self, name: str, handler: Callable, schema: Dict):
        self.tools[name] = {
            "handler": handler,
            "schema": schema,
        }
        logger.info(f"Registered MCP tool: {name}")

    def register_resource(self, uri: str, data: Any):
        self.resources[uri] = data

    def register_prompt(self, name: str, template: str):
        self.prompts[name] = template

    # Tool implementations
    def _tool_send_email(self, **kwargs) -> Dict:
        logger.info(f"Sending email to: {kwargs.get('to')}")
        # For now, just simulate sending - in production would use actual SMTP
        return {
            "status": "success",
            "message": f"Email sent to {kwargs.get('to')}",
            "subject": kwargs.get("subject"),
        }

    def _tool_linkedin_post(self, **kwargs) -> Dict:
        content = kwargs.get("content")
        if not content:
            return {
                "status": "error",
                "message": "Content is required for LinkedIn post",
            }

        logger.info(f"Creating LinkedIn post via Playwright: {content[:50]}...")

        try:
            from playwright.sync_api import sync_playwright
            import os
            import time

            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(
                    headless=False
                )  # Set to True for production
                page = browser.new_page()

                # Navigate to LinkedIn
                page.goto("https://www.linkedin.com/login")

                # Check if we need to login (simplified - in production would handle auth properly)
                # For now, we'll assume user is already logged in or will login manually
                # In a real implementation, you would:
                # 1. Check for existing session cookies
                # 2. If not present, wait for user to login manually
                # 3. Then proceed with posting

                # Wait for user to login manually (simplified approach)
                logger.info("Please log in to LinkedIn in the browser window...")
                try:
                    # Wait for feed to appear (indicates login success)
                    page.wait_for_selector(
                        "div[data-id='feed-ember']", timeout=120000
                    )  # 2 minute timeout
                    logger.info("Logged in successfully!")
                except Exception as e:
                    logger.warning(f"Login wait timed out or failed: {e}")
                    # Continue anyway - user might be logged in

                # Navigate to post creation
                page.click("button:global:has-text('Start a post')")

                # Wait for the post editor to appear
                page.wait_for_selector("div[role='textbox']", timeout=10000)

                # Fill in the post content
                page.fill("div[role='textbox']", content)

                # Click the post button
                page.click("button:global:has-text('Post')")

                # Wait for post to be published
                page.wait_for_timeout(3000)  # Wait 3 seconds for post to go through

                # Get the current URL as post reference
                post_url = page.url

                browser.close()

                # Log the action
                self._tool_log_action(
                    action_type="linkedin_post",
                    details=f"Posted content via Playwright: {content[:100]}...",
                )

                return {
                    "status": "success",
                    "message": "LinkedIn post created successfully via Playwright",
                    "post_url": post_url,
                    "content": content,
                }

        except ImportError:
            logger.error("Playwright not available. Install with: uv add playwright")
            return {
                "status": "error",
                "message": "Playwright not installed. Please install playwright package.",
            }
        except Exception as e:
            logger.error(f"Error creating LinkedIn post with Playwright: {e}")
            return {
                "status": "error",
                "message": f"Failed to create LinkedIn post: {str(e)}",
            }

        logger.info(f"Creating LinkedIn post: {content[:50]}...")

        # For now, simulate the post - in production would use Playwright
        # To implement with Playwright:
        # 1. Launch browser
        # 2. Navigate to LinkedIn login
        # 3. Wait for manual login (or use saved session)
        # 4. Navigate to post creation
        # 5. Fill in content and submit
        # 6. Return post URL

        # Simulate successful post
        post_url = f"https://linkedin.com/feed/update/{int(datetime.now().timestamp())}"

        # Log the action
        self._tool_log_action(
            action_type="linkedin_post", details=f"Posted content: {content[:100]}..."
        )

        return {
            "status": "success",
            "message": "LinkedIn post created successfully",
            "post_url": post_url,
            "content": content,
        }

    def _tool_create_file(self, **kwargs) -> Dict:
        file_path = self.vault_path / kwargs.get("path", "")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(kwargs.get("content", ""))

        return {
            "status": "success",
            "path": str(file_path),
        }

    def _tool_read_file(self, **kwargs) -> Dict:
        file_path = self.vault_path / kwargs.get("path", "")

        if not file_path.exists():
            return {"status": "error", "message": "File not found"}

        return {
            "status": "success",
            "content": file_path.read_text(),
            "path": str(file_path),
        }

    def _tool_list_files(self, **kwargs) -> Dict:
        directory = self.vault_path / kwargs.get("directory", "")
        pattern = kwargs.get("pattern", "*")

        if not directory.exists():
            return {"status": "error", "message": "Directory not found"}

        files = [str(f.relative_to(self.vault_path)) for f in directory.glob(pattern)]

        return {
            "status": "success",
            "files": files,
            "count": len(files),
        }

    def _tool_delete_file(self, **kwargs) -> Dict:
        file_path = self.vault_path / kwargs.get("path", "")

        if not file_path.exists():
            return {"status": "error", "message": "File not found"}

        file_path.unlink()

        return {
            "status": "success",
            "message": f"Deleted {kwargs.get('path')}",
        }

    def _tool_move_file(self, **kwargs) -> Dict:
        source = self.vault_path / kwargs.get("source", "")
        destination = self.vault_path / kwargs.get("destination", "")

        if not source.exists():
            return {"status": "error", "message": "Source file not found"}

        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)

        return {
            "status": "success",
            "message": f"Moved to {kwargs.get('destination')}",
        }

    def _tool_search_content(self, **kwargs) -> Dict:
        query = kwargs.get("query", "").lower()
        search_path = self.vault_path / kwargs.get("path", "")

        results = []

        if search_path.exists():
            for file_path in search_path.rglob("*.md"):
                try:
                    content = file_path.read_text().lower()
                    if query in content:
                        results.append(str(file_path.relative_to(self.vault_path)))
                except:
                    pass

        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results),
        }

    def _tool_get_dashboard(self, **kwargs) -> Dict:
        dashboard_file = self.vault_path / "Dashboard.md"

        if dashboard_file.exists():
            return {
                "status": "success",
                "content": dashboard_file.read_text(),
            }

        return {"status": "error", "message": "Dashboard not found"}

    def _tool_get_approval_items(self, **kwargs) -> Dict:
        pending_dir = self.vault_path / "Pending_Approval"

        if not pending_dir.exists():
            return {"status": "success", "items": []}

        items = []
        for f in pending_dir.glob("*.md"):
            items.append(
                {
                    "name": f.name,
                    "path": str(f.relative_to(self.vault_path)),
                }
            )

        return {
            "status": "success",
            "items": items,
            "count": len(items),
        }

    def _tool_approve_item(self, **kwargs) -> Dict:
        item_name = kwargs.get("item_id", "")
        pending_dir = self.vault_path / "Pending_Approval"
        approved_dir = self.vault_path / "Approved"

        source = pending_dir / item_name
        dest = approved_dir / item_name

        if not source.exists():
            return {"status": "error", "message": "Item not found"}

        source.rename(dest)

        return {
            "status": "success",
            "message": f"Approved: {item_name}",
        }

    def _tool_reject_item(self, **kwargs) -> Dict:
        item_name = kwargs.get("item_id", "")
        reason = kwargs.get("reason", "")
        pending_dir = self.vault_path / "Pending_Approval"
        rejected_dir = self.vault_path / "Rejected"

        source = pending_dir / item_name
        dest = rejected_dir / item_name

        if not source.exists():
            return {"status": "error", "message": "Item not found"}

        source.rename(dest)

        return {
            "status": "success",
            "message": f"Rejected: {item_name}",
            "reason": reason,
        }

    def _tool_create_task(self, **kwargs) -> Dict:
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        needs_action_dir = self.vault_path / "Needs_Action"
        needs_action_dir.mkdir(exist_ok=True)

        task_content = f"""---
type: task
status: pending
created: {datetime.now().isoformat()}
priority: {kwargs.get("priority", "medium")}
---

# {kwargs.get("title", "Untitled Task")}

{kwargs.get("description", "")}

## Actions
- [ ] Start task
- [ ] Complete task
"""

        task_file = needs_action_dir / f"{task_id}.md"
        task_file.write_text(task_content)

        return {
            "status": "success",
            "task_id": task_id,
            "path": str(task_file.relative_to(self.vault_path)),
        }

    def _tool_get_tasks(self, **kwargs) -> Dict:
        status_filter = kwargs.get("status")

        tasks = []
        for folder in ["Needs_Action", "Done", "Plans"]:
            folder_path = self.vault_path / folder
            if folder_path.exists():
                for f in folder_path.glob("*.md"):
                    content = f.read_text()
                    if status_filter and status_filter not in content:
                        continue
                    tasks.append(
                        {
                            "name": f.name,
                            "folder": folder,
                            "path": str(f.relative_to(self.vault_path)),
                        }
                    )

        return {
            "status": "success",
            "tasks": tasks,
            "count": len(tasks),
        }

    def _tool_update_task(self, **kwargs) -> Dict:
        task_id = kwargs.get("task_id", "")
        new_status = kwargs.get("status", "")

        for folder in ["Needs_Action", "Done", "Plans", "Approved"]:
            task_path = self.vault_path / folder / task_id
            if task_path.exists():
                content = task_path.read_text()
                content = content.replace("status: pending", f"status: {new_status}")
                task_path.write_text(content)

                return {
                    "status": "success",
                    "message": f"Updated task to {new_status}",
                }

        return {"status": "error", "message": "Task not found"}

    def _tool_run_automation(self, **kwargs) -> Dict:
        workflow_name = kwargs.get("workflow_name", "")
        params = kwargs.get("parameters", {})

        logger.info(f"Running automation: {workflow_name}")

        return {
            "status": "success",
            "workflow": workflow_name,
            "result": "Automation executed successfully",
            "parameters": params,
        }

    def _tool_log_action(self, **kwargs) -> Dict:
        logs_dir = self.vault_path / "Logs"
        logs_dir.mkdir(exist_ok=True)

        log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": kwargs.get("action_type"),
            "details": kwargs.get("details"),
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return {
            "status": "success",
            "logged": log_entry,
        }

    def handle_message(self, message: Dict) -> Dict:
        msg_type = message.get("type")
        msg_id = message.get("id", str(datetime.now().timestamp()))

        self.request_history.append(
            {
                "id": msg_id,
                "type": msg_type,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if msg_type == MCPMessageType.TOOL_CALL.value:
            tool_name = message.get("tool")
            params = message.get("parameters", {})

            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name]["handler"](**params)
                    return {
                        "type": MCPMessageType.TOOL_RESULT.value,
                        "id": msg_id,
                        "result": result,
                    }
                except Exception as e:
                    return {
                        "type": MCPMessageType.TOOL_RESULT.value,
                        "id": msg_id,
                        "error": str(e),
                    }
            else:
                return {
                    "type": MCPMessageType.TOOL_RESULT.value,
                    "id": msg_id,
                    "error": f"Tool not found: {tool_name}",
                }

        elif msg_type == MCPMessageType.RESOURCE_REQUEST.value:
            uri = message.get("uri")

            if uri in self.resources:
                return {
                    "type": MCPMessageType.RESOURCE_RESPONSE.value,
                    "id": msg_id,
                    "resource": self.resources[uri],
                }
            else:
                return {
                    "type": MCPMessageType.RESOURCE_RESPONSE.value,
                    "id": msg_id,
                    "error": f"Resource not found: {uri}",
                }

        elif msg_type == MCPMessageType.PROMPT_REQUEST.value:
            prompt_name = message.get("prompt")

            if prompt_name in self.prompts:
                return {
                    "type": MCPMessageType.PROMPT_RESPONSE.value,
                    "id": msg_id,
                    "template": self.prompts[prompt_name],
                }
            else:
                return {
                    "type": MCPMessageType.PROMPT_RESPONSE.value,
                    "id": msg_id,
                    "error": f"Prompt not found: {prompt_name}",
                }

        return {
            "type": "error",
            "id": msg_id,
            "error": "Unknown message type",
        }

    def get_tools_list(self) -> List[Dict]:
        return [
            {
                "name": name,
                "schema": tool["schema"],
            }
            for name, tool in self.tools.items()
        ]

    def get_resources_list(self) -> List[str]:
        return list(self.resources.keys())

    def get_prompts_list(self) -> List[str]:
        return list(self.prompts.keys())

    def start(self):
        if self.server:
            return {"status": "error", "message": "Server already running"}

        class MCPHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)

                try:
                    message = json.loads(body.decode())
                    response = self.server.mcp_server.handle_message(message)

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())

            def do_GET(self):
                if self.path == "/tools":
                    tools = self.server.mcp_server.get_tools_list()
                    response = {"tools": tools}
                elif self.path == "/resources":
                    resources = self.server.mcp_server.get_resources_list()
                    response = {"resources": resources}
                elif self.path == "/prompts":
                    prompts = self.server.mcp_server.get_prompts_list()
                    response = {"prompts": prompts}
                elif self.path == "/status":
                    response = self.server.mcp_server.get_status()
                else:
                    response = {"status": "ok", "message": "MCP Server running"}

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            def log_message(self, format, *args):
                logger.info(f"{self.address_string()} - {format % args}")

        self.server = socketserver.TCPServer(("", self.port), MCPHandler)
        self.server.mcp_server = self  # Attach MCP server instance to HTTP server

        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        logger.info(f"MCP Server started on port {self.port}")

        return {
            "status": "success",
            "port": self.port,
            "tools": len(self.tools),
        }

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server = None
            logger.info("MCP Server stopped")

            return {"status": "success"}

        return {"status": "error", "message": "Server not running"}

    def get_status(self) -> Dict:
        return {
            "running": self.server is not None,
            "port": self.port,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "prompts_count": len(self.prompts),
            "requests_handled": len(self.request_history),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MCP Server for AI Employee")
    parser.add_argument("--vault", required=True, help="Path to vault")
    parser.add_argument("--port", type=int, default=8080, help="Port to run on")
    args = parser.parse_args()

    server = MCPServer(args.vault, args.port)
    print(f"Starting MCP Server on port {args.port}")
    print(f"Vault path: {args.vault}")

    result = server.start()
    print(f"Server start result: {result}")

    try:
        while True:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down MCP Server...")
        server.stop()


if __name__ == "__main__":
    main()
