#!/usr/bin/env python3
"""
Enhanced Audit Logger for AI Employee Vault (Gold Tier)
Provides comprehensive audit logging with error recovery and graceful degradation
"""

import json
import logging
import traceback
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import threading
import time

logger = logging.getLogger("EnhancedAuditLogger")


class AuditLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    SYSTEM = "system"
    ACTION = "action"
    APPROVAL = "approval"
    ERROR = "error"
    SECURITY = "security"
    PERFORMANCE = "performance"


class EnhancedAuditLogger:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Enhanced logging files
        self.daily_log_file = (
            self.logs_dir / f"audit_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        )
        self.error_log_file = self.logs_dir / "errors.jsonl"
        self.performance_log_file = self.logs_dir / "performance.jsonl"
        self.security_log_file = self.logs_dir / "security.jsonl"

        # In-memory buffers for performance
        self.action_buffer = []
        self.error_buffer = []
        self.performance_buffer = []
        self.security_buffer = []

        # Buffer flush settings
        self.buffer_size = 10
        self.flush_interval = 30  # seconds

        # Start background flush thread
        self.flush_thread = threading.Thread(target=self._background_flush, daemon=True)
        self.flush_thread.start()

        logger.info("EnhancedAuditLogger initialized - Gold Tier")

    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()

    def _write_to_file(self, file_path: Path, entry: Dict):
        """Write entry to log file with error recovery"""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write entry as JSON line
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            # Fallback: try to write to a backup location
            try:
                backup_path = self.vault_path / "Logs" / "backup" / file_path.name
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                with open(backup_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                logger.warning(f"Wrote audit log to backup due to error: {e}")
            except Exception as backup_error:
                logger.error(f"Failed to write to backup audit log: {backup_error}")

    def _background_flush(self):
        """Background thread to flush buffers periodically"""
        while True:
            try:
                time.sleep(self.flush_interval)
                self.flush_buffers()
            except Exception as e:
                logger.error(f"Error in audit logger background flush: {e}")

    def flush_buffers(self):
        """Flush all buffers to disk"""
        try:
            if self.action_buffer:
                for entry in self.action_buffer:
                    self._write_to_file(self.daily_log_file, entry)
                self.action_buffer.clear()

            if self.error_buffer:
                for entry in self.error_buffer:
                    self._write_to_file(self.error_log_file, entry)
                self.error_buffer.clear()

            if self.performance_buffer:
                for entry in self.performance_buffer:
                    self._write_to_file(self.performance_log_file, entry)
                self.performance_buffer.clear()

            if self.security_buffer:
                for entry in self.security_buffer:
                    self._write_to_file(self.security_log_file, entry)
                self.security_buffer.clear()

        except Exception as e:
            logger.error(f"Error flushing audit buffers: {e}")

    def log_action(
        self,
        action_type: str,
        details: str,
        level: AuditLevel = AuditLevel.INFO,
        category: AuditCategory = AuditCategory.ACTION,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Log an action with enhanced metadata"""
        try:
            entry = {
                "timestamp": self._get_timestamp(),
                "action_type": action_type,
                "details": details,
                "level": level.value,
                "category": category.value,
                "metadata": metadata or {},
                "process_id": os.getpid(),
                "thread_id": threading.get_ident(),
            }

            # Add to appropriate buffer
            if level in [AuditLevel.ERROR, AuditLevel.CRITICAL]:
                self.error_buffer.append(entry)
            elif category == AuditCategory.PERFORMANCE:
                self.performance_buffer.append(entry)
            elif category == AuditCategory.SECURITY:
                self.security_buffer.append(entry)
            else:
                self.action_buffer.append(entry)

            # Flush if buffer is full
            if (
                len(self.action_buffer) >= self.buffer_size
                or len(self.error_buffer) >= self.buffer_size
                or len(self.performance_buffer) >= self.buffer_size
                or len(self.security_buffer) >= self.buffer_size
            ):
                self.flush_buffers()

            return {
                "status": "success",
                "logged": entry,
                "buffer_sizes": {
                    "action": len(self.action_buffer),
                    "error": len(self.error_buffer),
                    "performance": len(self.performance_buffer),
                    "security": len(self.security_buffer),
                },
            }
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return {"status": "error", "message": str(e)}

    def log_error(
        self,
        error_type: str,
        error_message: str,
        traceback_str: Optional[str] = None,
        context: Optional[Dict] = None,
        recoverable: bool = True,
    ) -> Dict:
        """Log an error with traceback and recovery information"""
        try:
            entry = {
                "timestamp": self._get_timestamp(),
                "error_type": error_type,
                "error_message": error_message,
                "traceback": traceback_str or traceback.format_exc(),
                "context": context or {},
                "recoverable": recoverable,
                "process_id": os.getpid(),
                "thread_id": threading.get_ident(),
            }

            self.error_buffer.append(entry)

            # Also log to action log for completeness
            action_entry = {
                "timestamp": self._get_timestamp(),
                "action_type": "error_occurred",
                "details": f"{error_type}: {error_message}",
                "level": AuditLevel.ERROR.value,
                "category": AuditCategory.ERROR.value,
                "metadata": {"error_id": hash(str(entry)) % 10000},
                "process_id": os.getpid(),
                "thread_id": threading.get_ident(),
            }
            self.action_buffer.append(action_entry)

            # Immediate flush for errors
            if len(self.error_buffer) >= 1:  # Flush errors immediately
                self.flush_buffers()

            return {
                "status": "success",
                "logged": entry,
                "error_id": hash(str(entry)) % 10000,
            }
        except Exception as e:
            logger.error(f"Error logging error: {e}")
            return {"status": "error", "message": str(e)}

    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Log performance metrics"""
        try:
            entry = {
                "timestamp": self._get_timestamp(),
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "metadata": metadata or {},
                "process_id": os.getpid(),
                "thread_id": threading.get_ident(),
            }

            self.performance_buffer.append(entry)

            # Flush if buffer is full
            if len(self.performance_buffer) >= self.buffer_size:
                self.flush_buffers()

            return {"status": "success", "logged": entry}
        except Exception as e:
            logger.error(f"Error logging performance: {e}")
            return {"status": "error", "message": str(e)}

    def log_security_event(
        self,
        event_type: str,
        details: str,
        severity: AuditLevel = AuditLevel.WARNING,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Log security-related events"""
        try:
            entry = {
                "timestamp": self._get_timestamp(),
                "event_type": event_type,
                "details": details,
                "severity": severity.value,
                "metadata": metadata or {},
                "process_id": os.getpid(),
                "thread_id": threading.get_ident(),
            }

            self.security_buffer.append(entry)

            # Also log to error buffer if high severity
            if severity in [AuditLevel.ERROR, AuditLevel.CRITICAL]:
                self.error_buffer.append(entry)

            # Flush if buffer is full
            if len(self.security_buffer) >= self.buffer_size:
                self.flush_buffers()

            return {"status": "success", "logged": entry}
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
            return {"status": "error", "message": str(e)}

    def get_recent_logs(
        self, log_type: str = "daily", hours: int = 24, limit: int = 100
    ) -> List[Dict]:
        """Get recent logs from specified log type"""
        try:
            logs = []
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Determine which file to read
            if log_type == "daily":
                file_path = self.daily_log_file
            elif log_type == "error":
                file_path = self.error_log_file
            elif log_type == "performance":
                file_path = self.performance_log_file
            elif log_type == "security":
                file_path = self.security_log_file
            else:
                # Default to daily log
                file_path = self.daily_log_file

            if not file_path.exists():
                return []

            # Read lines and filter by time
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        if entry_time >= cutoff_time:
                            logs.append(entry)
                            if len(logs) >= limit:
                                break
                    except (json.JSONDecodeError, KeyError, ValueError):
                        # Skip malformed lines
                        continue

            # Sort by timestamp (newest first)
            logs.sort(key=lambda x: x["timestamp"], reverse=True)
            return logs[:limit]
        except Exception as e:
            logger.error(f"Error retrieving recent logs: {e}")
            return []

    def get_error_summary(self, hours: int = 24) -> Dict:
        """Get summary of errors in the last N hours"""
        try:
            errors = self.get_recent_logs("error", hours=hours, limit=1000)

            # Group by error type
            error_types = {}
            for error in errors:
                error_type = error.get("error_type", "unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1

            return {
                "time_period_hours": hours,
                "total_errors": len(errors),
                "error_types": error_types,
                "recent_errors": errors[:10],  # Most recent 10
            }
        except Exception as e:
            logger.error(f"Error generating error summary: {e}")
            return {"status": "error", "message": str(e)}

    def get_performance_summary(self, hours: int = 24) -> Dict:
        """Get summary of performance metrics in the last N hours"""
        try:
            performances = self.get_recent_logs("performance", hours=hours, limit=1000)

            if not performances:
                return {
                    "time_period_hours": hours,
                    "total_operations": 0,
                    "avg_duration_ms": 0,
                    "success_rate": 0,
                }

            # Calculate statistics
            durations = [p.get("duration_ms", 0) for p in performances]
            successes = [p.get("success", False) for p in performances]

            avg_duration = sum(durations) / len(durations) if durations else 0
            success_rate = sum(successes) / len(successes) if successes else 0

            # Group by operation type
            operations = {}
            for perf in performances:
                op = perf.get("operation", "unknown")
                if op not in operations:
                    operations[op] = {"count": 0, "total_duration": 0, "successes": 0}
                operations[op]["count"] += 1
                operations[op]["total_duration"] += perf.get("duration_ms", 0)
                if perf.get("success", False):
                    operations[op]["successes"] += 1

            # Format operations summary
            ops_summary = {}
            for op, data in operations.items():
                ops_summary[op] = {
                    "count": data["count"],
                    "avg_duration_ms": data["total_duration"] / data["count"]
                    if data["count"] > 0
                    else 0,
                    "success_rate": data["successes"] / data["count"]
                    if data["count"] > 0
                    else 0,
                }

            return {
                "time_period_hours": hours,
                "total_operations": len(performances),
                "avg_duration_ms": avg_duration,
                "success_rate": success_rate,
                "operations": ops_summary,
            }
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"status": "error", "message": str(e)}

    def shutdown(self):
        """Shutdown the audit logger, flushing all buffers"""
        try:
            self.flush_buffers()
            logger.info("EnhancedAuditLogger shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down EnhancedAuditLogger: {e}")


# Global instance for easy access
_audit_logger_instance = None


def get_audit_logger(vault_path: str) -> EnhancedAuditLogger:
    """Get or create the global audit logger instance"""
    global _audit_logger_instance
    if _audit_logger_instance is None or _audit_logger_instance.vault_path != Path(
        vault_path
    ):
        _audit_logger_instance = EnhancedAuditLogger(vault_path)
    return _audit_logger_instance
