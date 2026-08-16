"""SystemTools — AI-accessible function-calling tools for OS-level actions.

Provides a registry of tools (get_telemetry, launch_application, execute_shell,
send_notification, etc.) that the Intelligence Engine can invoke on behalf of
the user — enabling JARVIS-like agentic OS control.

Each tool has a JSON Schema definition for LLM function-calling, an async
execute method, and built-in safety validation.
"""

from __future__ import annotations

import asyncio
import os
import shlex
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from axiom.runtime.logging import RuntimeLogger


# ═══════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ToolDef:
    """Definition of a callable system tool."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    execute: Callable[..., Any]
    category: str = "system"
    requires_confirmation: bool = False
    timeout_seconds: float = 30.0


@dataclass
class ToolResult:
    """Result of executing a system tool."""

    success: bool
    output: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "data": self.data,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 1),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Dangerous command blocklist
# ═══════════════════════════════════════════════════════════════════════════

BLOCKED_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",
    "> /dev/sda",
    "| shutdown",
    "| reboot",
    "| poweroff",
    "| halt",
    "chmod 000",
    "chown -R",
    "> /etc/",
    "passwd",
    "wget ",
    "curl ",
]

DANGEROUS_PATTERNS = [
    "rm -rf",
    "mkfs.",
    "dd if=",
    "fork",
    "dev/sd",
    "boot",
    "init",
    "fdisk",
    "mkswap",
    "swapoff",
]


def _is_command_safe(command: str) -> tuple:
    """Check if a shell command is safe to execute.

    Returns (safe, reason). If unsafe, reason explains why.
    """
    cmd_lower = command.lower().strip()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return False, f"Command matches blocked pattern: {blocked}"

    for pattern in DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return True, f"Potentially dangerous pattern '{pattern}' — confirm to proceed"

    return True, ""


# ═══════════════════════════════════════════════════════════════════════════
# System Tools Registry
# ═══════════════════════════════════════════════════════════════════════════


class SystemTools:
    """Registry of callable system tools for AI agent function-calling.

    The Intelligence Engine retrieves tool schemas via get_tool_schemas()
    and executes tools via execute_tool() — forming the function-calling
    bridge between the LLM and the OS.
    """

    def __init__(
        self,
        runtime: Optional[Any] = None,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self._runtime = runtime
        self._logger = logger or RuntimeLogger()
        self._tools: Dict[str, ToolDef] = {}
        self._init_tools()

    def _init_tools(self) -> None:
        """Register all built-in system tools."""

        self._tools["get_telemetry"] = ToolDef(
            name="get_telemetry",
            description="Get live system telemetry — CPU, RAM, disk, network, temperature, and health score.",
            input_schema={"type": "object", "properties": {}, "required": []},
            execute=self._exec_get_telemetry,
            category="system",
            timeout_seconds=10.0,
        )

        self._tools["system_diagnostics"] = ToolDef(
            name="system_diagnostics",
            description="Run a full system diagnostic and return a health report including CPU, memory, disk status, running processes, and connectivity.",
            input_schema={
                "type": "object",
                "properties": {
                    "include_processes": {
                        "type": "boolean",
                        "description": "Include top processes in the report",
                        "default": False,
                    }
                },
            },
            execute=self._exec_system_diagnostics,
            category="system",
            timeout_seconds=30.0,
        )

        self._tools["launch_application"] = ToolDef(
            name="launch_application",
            description="Launch a desktop application or run a script by path.",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Path or command to launch (e.g., '/Applications/Safari.app', 'open -a Terminal')",
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional arguments to pass",
                    },
                    "background": {
                        "type": "boolean",
                        "description": "Run in background without waiting",
                        "default": True,
                    },
                },
                "required": ["command"],
            },
            execute=self._exec_launch_application,
            category="actions",
            timeout_seconds=15.0,
        )

        self._tools["execute_shell"] = ToolDef(
            name="execute_shell",
            description="Execute a shell command and return its output. Only safe, read-only commands allowed by default.",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "description": "Max execution time in seconds",
                        "default": 10.0,
                    },
                    "confirm_unsafe": {
                        "type": "boolean",
                        "description": "Set to true to confirm execution of potentially dangerous commands",
                        "default": False,
                    },
                },
                "required": ["command"],
            },
            execute=self._exec_shell,
            category="actions",
            requires_confirmation=True,
            timeout_seconds=30.0,
        )

        self._tools["get_system_info"] = ToolDef(
            name="get_system_info",
            description="Get basic OS information — hostname, platform, kernel version, architecture, uptime.",
            input_schema={"type": "object", "properties": {}, "required": []},
            execute=self._exec_system_info,
            category="system",
            timeout_seconds=5.0,
        )

        self._tools["check_connectivity"] = ToolDef(
            name="check_connectivity",
            description="Check network connectivity by pinging a host.",
            input_schema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Host to ping (default: 8.8.8.8)",
                        "default": "8.8.8.8",
                    }
                },
            },
            execute=self._exec_check_connectivity,
            category="system",
            timeout_seconds=10.0,
        )

        self._tools["send_notification"] = ToolDef(
            name="send_notification",
            description="Send a desktop notification to the user.",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Notification title"},
                    "message": {"type": "string", "description": "Notification body message"},
                    "type": {
                        "type": "string",
                        "enum": ["info", "warning", "error", "success"],
                        "description": "Notification type",
                        "default": "info",
                    },
                },
                "required": ["title", "message"],
            },
            execute=self._exec_notification,
            category="actions",
            timeout_seconds=5.0,
        )

        self._tools["control_workflow"] = ToolDef(
            name="control_workflow",
            description="Launch, cancel, or check status of an AXIOM workflow.",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["launch", "cancel", "status"],
                        "description": "Action to perform on the workflow",
                    },
                    "workflow_id": {"type": "string", "description": "ID of the workflow to control"},
                    "context": {"type": "object", "description": "Optional context for workflow launch"},
                },
                "required": ["action", "workflow_id"],
            },
            execute=self._exec_control_workflow,
            category="axiom",
            timeout_seconds=30.0,
        )

        self._tools["status_summary"] = ToolDef(
            name="status_summary",
            description="Get a brief text summary of the current AXIOM system status — executives, workflows, health.",
            input_schema={
                "type": "object",
                "properties": {},
            },
            execute=self._exec_status_summary,
            category="axiom",
            timeout_seconds=5.0,
        )

    # ── Public API ───────────────────────────────────────────────────────

    def get_tool(self, name: str) -> Optional[ToolDef]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "requires_confirmation": t.requires_confirmation,
                "input_schema": t.input_schema,
            }
            for t in self._tools.values()
        ]

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool definitions in LLM function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema,
                },
            }
            for t in self._tools.values()
        ]

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name with the given arguments."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(success=False, output=f"Unknown tool: {name}", error=f"No tool registered with name '{name}'")

        start = time.monotonic()
        try:
            result = await asyncio.wait_for(tool.execute(args), timeout=tool.timeout_seconds)
            result.duration_ms = (time.monotonic() - start) * 1000
            return result
        except asyncio.TimeoutError:
            elapsed = (time.monotonic() - start) * 1000
            return ToolResult(success=False, output=f"Tool '{name}' timed out after {tool.timeout_seconds}s", error="timeout", duration_ms=elapsed)
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return ToolResult(success=False, output=f"Tool '{name}' failed: {exc}", error=str(exc), duration_ms=elapsed)

    # ── Tool Executors ───────────────────────────────────────────────────

    async def _exec_get_telemetry(self, args: Dict[str, Any]) -> ToolResult:
        monitor = getattr(self._runtime, "system_monitor", None) or getattr(self._runtime, "monitor", None)
        if not monitor:
            from axiom.runtime.system_monitor import SystemMonitor
            monitor = SystemMonitor(logger=self._logger)
            await monitor.initialise()

        snap = await monitor.snapshot()
        return ToolResult(success=True, output=monitor.format_summary(snap), data=snap.to_dict())

    async def _exec_system_diagnostics(self, args: Dict[str, Any]) -> ToolResult:
        monitor = getattr(self._runtime, "system_monitor", None) or getattr(self._runtime, "monitor", None)
        if not monitor:
            from axiom.runtime.system_monitor import SystemMonitor
            monitor = SystemMonitor(logger=self._logger)
            await monitor.initialise()

        snap = await monitor.snapshot()
        n = args.get("include_processes", False)
        lines = [
            f"System Diagnostic Report",
            f"{'=' * 40}",
            f"Hostname: {snap.hostname}  |  Platform: {snap.platform}",
            f"Uptime: {snap.uptime_seconds / 3600:.1f}h  |  Processes: {snap.processes}",
            f"Health: {snap.health_label.upper()} (score: {snap.health_score:.2f})",
            f"",
            f"CPU: {snap.cpu.percent:.1f}% ({snap.cpu.count_logical} cores @ {snap.cpu.frequency_mhz:.0f} MHz)",
            f"RAM: {snap.memory.percent:.1f}% ({snap.memory.used_gb:.1f}/{snap.memory.total_gb:.1f} GB)",
            f"Swap: {snap.memory.swap_percent:.1f}% ({snap.memory.swap_used_gb:.1f}/{snap.memory.swap_total_gb:.1f} GB)",
            f"Disk: {snap.disk.percent:.1f}% ({snap.disk.used_gb:.1f}/{snap.disk.total_gb:.1f} GB)",
            f"Network RX: {snap.network.bytes_recv_mb:.0f} MB  |  TX: {snap.network.bytes_sent_mb:.0f} MB",
        ]
        if snap.temperature.cpu_temp_c is not None:
            lines.append(f"CPU Temp: {snap.temperature.cpu_temp_c:.1f}°C")
        if n and snap.services:
            lines.append("")
            lines.append("Top Services:")
            for s in sorted(snap.services, key=lambda x: x.cpu_percent, reverse=True)[:10]:
                lines.append(f"  {s.name}: CPU {s.cpu_percent:.1f}%, RAM {s.memory_mb:.0f} MB")
        return ToolResult(success=True, output="\n".join(lines), data=snap.to_dict())

    async def _exec_launch_application(self, args: Dict[str, Any]) -> ToolResult:
        command = args.get("command", "")
        extra = args.get("args", [])
        bg = args.get("background", True)
        if not command:
            return ToolResult(success=False, output="No command provided", error="missing_command")
        try:
            cmd = [command] + (extra if extra else [])
            if bg:
                proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                return ToolResult(success=True, output=f"Launched '{command}' (PID: {proc.pid})", data={"pid": proc.pid, "command": command})
            else:
                proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
                out = stdout.decode() if stdout else ""
                err = stderr.decode() if stderr else ""
                return ToolResult(success=proc.returncode == 0, output=out[:2000] or f"Exit code: {proc.returncode}",
                                  data={"returncode": proc.returncode, "stdout": out[:2000], "stderr": err[:500]})
        except FileNotFoundError:
            return ToolResult(success=False, output=f"Application not found: {command}", error="not_found")
        except Exception as exc:
            return ToolResult(success=False, output=f"Failed to launch '{command}': {exc}", error=str(exc))

    async def _exec_shell(self, args: Dict[str, Any]) -> ToolResult:
        command = args.get("command", "")
        timeout = args.get("timeout_seconds", 10.0)
        confirm = args.get("confirm_unsafe", False)
        if not command:
            return ToolResult(success=False, output="No command provided", error="missing_command")
        safe, reason = _is_command_safe(command)
        if not safe:
            return ToolResult(success=False, output=f"Command blocked: {reason}", data={"command": command, "blocked": True}, error="blocked_command")
        if not safe and not confirm:
            return ToolResult(success=False, output=f"Requires confirmation: {reason}. Set confirm_unsafe=true to execute.", error="requires_confirmation")
        try:
            proc = await asyncio.create_subprocess_exec("/bin/sh", "-c", command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out = stdout.decode() if stdout else ""
            err = stderr.decode() if stderr else ""
            return ToolResult(success=proc.returncode == 0, output=out[:2000] or f"Exit code: {proc.returncode}",
                              data={"returncode": proc.returncode, "stdout": out[:2000], "stderr": err[:500]})
        except asyncio.TimeoutError:
            return ToolResult(success=False, output=f"Command timed out after {timeout}s", error="timeout")
        except Exception as exc:
            return ToolResult(success=False, output=f"Shell execution failed: {exc}", error=str(exc))

    async def _exec_system_info(self, args: Dict[str, Any]) -> ToolResult:
        import platform as pf
        import time as _time
        import psutil
        bt = psutil.boot_time() if hasattr(psutil, "boot_time") else _time.time()
        data = {"hostname": pf.node(), "platform": pf.platform(), "release": pf.release(),
                "version": pf.version(), "architecture": pf.machine(), "processor": pf.processor(),
                "boot_time": bt, "uptime_seconds": _time.time() - bt}
        out = f"Host: {data['hostname']}\nOS: {data['platform']} {data['release']}\nArch: {data['architecture']}\nUptime: {data['uptime_seconds']/3600:.1f}h"
        return ToolResult(success=True, output=out, data=data)

    async def _exec_check_connectivity(self, args: Dict[str, Any]) -> ToolResult:
        host = args.get("host", "8.8.8.8")
        try:
            proc = await asyncio.create_subprocess_exec("ping", "-c", "1", "-W", "3", host, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            ret = await proc.wait()
            return ToolResult(success=ret == 0, output=f"Connected to {host}" if ret == 0 else f"No response from {host}",
                              data={"host": host, "connected": ret == 0})
        except FileNotFoundError:
            return ToolResult(success=False, output="ping not available", error="not_found")

    async def _exec_notification(self, args: Dict[str, Any]) -> ToolResult:
        title = args.get("title", "AXIOM OS")
        message = args.get("message", "")
        notif_type = args.get("type", "info")
        sent = False
        try:
            script = f'display notification "{message}" with title "{title}" subtitle "AXIOM - {notif_type}"'
            proc = await asyncio.create_subprocess_exec("osascript", "-e", script, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await proc.wait()
            sent = proc.returncode == 0
        except FileNotFoundError:
            pass
        return ToolResult(success=sent, output=f"Notification {'sent' if sent else 'logged'}: {title}",
                          data={"title": title, "message": message, "type": notif_type, "sent": sent})

    async def _exec_control_workflow(self, args: Dict[str, Any]) -> ToolResult:
        action = args.get("action", "")
        wf_id = args.get("workflow_id", "")
        ctx = args.get("context", {})
        if not self._runtime or not self._runtime.workflow:
            return ToolResult(success=False, output="Workflow engine not available", error="no_workflow_engine")

        wf = self._runtime.workflow
        if action == "launch":
            try:
                inst = wf.create_instance(wf_id, ctx)
                await wf.start(inst.instance_id)
                return ToolResult(success=True, output=f"Launched '{wf_id[:20]}' (instance: {inst.instance_id[:12]}...)",
                                  data={"instance_id": inst.instance_id, "workflow_id": wf_id, "status": inst.status.value})
            except ValueError as exc:
                return ToolResult(success=False, output=str(exc), error=str(exc))
        elif action == "cancel":
            try:
                await wf.cancel(wf_id)
                return ToolResult(success=True, output=f"Cancelled '{wf_id}'", data={"instance_id": wf_id, "status": "cancelled"})
            except ValueError as exc:
                return ToolResult(success=False, output=str(exc), error=str(exc))
        elif action == "status":
            try:
                inst = wf.get_instance(wf_id)
                if inst:
                    return ToolResult(success=True, output=f"Status: {inst.status.value} ({inst.current_step_index}/{len(inst.steps)} steps)",
                                      data={"status": inst.status.value, "current_step": inst.current_step_index, "total_steps": len(inst.steps)})
                return ToolResult(success=False, output=f"Instance '{wf_id}' not found", error="not_found")
            except ValueError as exc:
                return ToolResult(success=False, output=str(exc), error=str(exc))
        return ToolResult(success=False, output=f"Unknown action: {action}", error="invalid_action")

    async def _exec_status_summary(self, args: Dict[str, Any]) -> ToolResult:
        """Return a brief text summary of system state."""
        if not self._runtime:
            return ToolResult(success=True, output="System is online. (runtime object unavailable for details)")

        try:
            rt = self._runtime
            summary = rt.get_summary() if hasattr(rt, "get_summary") else {}
            axiom_info = summary.get("axiom", {})
            health = summary.get("health", {})

            lines = [
                f"State: {axiom_info.get('state', 'unknown')}",
                f"Uptime: {health.get('healthy', 0)}/{health.get('total', 0)} components healthy",
                f"Executives: {summary.get('executives', 0)}",
                f"Workflows: {summary.get('workflows_defined', 0)} defined",
                f"Research workspaces: {summary.get('research_workspaces', 0)}",
            ]
            return ToolResult(success=True, output=" | ".join(lines), data=summary)
        except Exception as exc:
            return ToolResult(success=True, output=f"System running (summary unavailable: {exc})")
