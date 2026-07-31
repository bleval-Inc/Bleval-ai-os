"""System Monitor — async OS telemetry for AXIOM AI.

Provides real-time CPU, RAM, disk, network, temperature, and process
information for the intelligence engine and boot greeting engine.

Uses psutil when available (production) with graceful fallback to
/proc and sysctl for environments without the package.
"""

from __future__ import annotations

import asyncio
import os
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from axiom.runtime.logging import RuntimeLogger


# ═══════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class CpuInfo:
    percent: float = 0.0
    per_core: List[float] = field(default_factory=list)
    count_logical: int = 0
    count_physical: int = 0
    frequency_mhz: float = 0.0
    load_avg_1m: float = 0.0
    load_avg_5m: float = 0.0
    load_avg_15m: float = 0.0


@dataclass
class MemoryInfo:
    total_gb: float = 0.0
    used_gb: float = 0.0
    available_gb: float = 0.0
    percent: float = 0.0
    swap_total_gb: float = 0.0
    swap_used_gb: float = 0.0
    swap_percent: float = 0.0


@dataclass
class DiskInfo:
    total_gb: float = 0.0
    used_gb: float = 0.0
    free_gb: float = 0.0
    percent: float = 0.0
    mount_point: str = "/"


@dataclass
class NetworkInfo:
    bytes_sent_mb: float = 0.0
    bytes_recv_mb: float = 0.0
    packets_sent: int = 0
    packets_recv: int = 0
    connections: int = 0
    interfaces: List[str] = field(default_factory=list)


@dataclass
class TemperatureInfo:
    cpu_temp_c: Optional[float] = None
    gpu_temp_c: Optional[float] = None
    battery_temp_c: Optional[float] = None
    ambient_c: Optional[float] = None


@dataclass
class ServiceInfo:
    name: str = ""
    status: str = "unknown"  # running, stopped, error
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    uptime_seconds: float = 0.0


@dataclass
class TelemetrySnapshot:
    """Complete system telemetry snapshot at a point in time."""

    timestamp: float = 0.0
    cpu: CpuInfo = field(default_factory=CpuInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    disk: DiskInfo = field(default_factory=DiskInfo)
    network: NetworkInfo = field(default_factory=NetworkInfo)
    temperature: TemperatureInfo = field(default_factory=TemperatureInfo)
    hostname: str = ""
    platform: str = ""
    uptime_seconds: float = 0.0
    boot_time: float = 0.0
    processes: int = 0
    services: List[ServiceInfo] = field(default_factory=list)

    @property
    def health_score(self) -> float:
        """Normalised health score 0.0–1.0 based on CPU, RAM, disk."""
        cpu_health = max(0.0, 1.0 - (self.cpu.percent / 100.0))
        mem_health = max(0.0, 1.0 - (self.memory.percent / 100.0))
        disk_health = max(0.0, 1.0 - (self.disk.percent / 100.0))
        return round((cpu_health + mem_health + disk_health) / 3.0, 4)

    @property
    def health_label(self) -> str:
        score = self.health_score
        if score >= 0.8:
            return "healthy"
        if score >= 0.5:
            return "degraded"
        return "critical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "platform": self.platform,
            "uptime_seconds": self.uptime_seconds,
            "boot_time": self.boot_time,
            "processes": self.processes,
            "health_score": self.health_score,
            "health_label": self.health_label,
            "cpu": {
                "percent": self.cpu.percent,
                "per_core": self.cpu.per_core,
                "count_logical": self.cpu.count_logical,
                "count_physical": self.cpu.count_physical,
                "frequency_mhz": self.cpu.frequency_mhz,
                "load_avg": [
                    self.cpu.load_avg_1m,
                    self.cpu.load_avg_5m,
                    self.cpu.load_avg_15m,
                ],
            },
            "memory": {
                "total_gb": round(self.memory.total_gb, 2),
                "used_gb": round(self.memory.used_gb, 2),
                "available_gb": round(self.memory.available_gb, 2),
                "percent": self.memory.percent,
                "swap_total_gb": round(self.memory.swap_total_gb, 2),
                "swap_used_gb": round(self.memory.swap_used_gb, 2),
            },
            "disk": {
                "total_gb": round(self.disk.total_gb, 2),
                "used_gb": round(self.disk.used_gb, 2),
                "free_gb": round(self.disk.free_gb, 2),
                "percent": self.disk.percent,
                "mount_point": self.disk.mount_point,
            },
            "network": {
                "bytes_sent_mb": round(self.network.bytes_sent_mb, 2),
                "bytes_recv_mb": round(self.network.bytes_recv_mb, 2),
                "packets_sent": self.network.packets_sent,
                "packets_recv": self.network.packets_recv,
                "connections": self.network.connections,
                "interfaces": self.network.interfaces,
            },
            "temperature": {
                "cpu_temp_c": self.temperature.cpu_temp_c,
                "gpu_temp_c": self.temperature.gpu_temp_c,
            },
            "services": [
                {
                    "name": s.name,
                    "status": s.status,
                    "pid": s.pid,
                    "cpu_percent": round(s.cpu_percent, 1),
                    "memory_mb": round(s.memory_mb, 1),
                    "uptime_seconds": round(s.uptime_seconds, 1),
                }
                for s in self.services
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# System Monitor Engine
# ═══════════════════════════════════════════════════════════════════════════


class SystemMonitor:
    """Async system telemetry collector.

    Collects CPU, RAM, disk, network, temperature, and process data.
    Uses psutil when installed (recommended), falls back to /proc + sysctl.

    The AI (IntelligenceEngine, GreetingEngine) calls snapshot() to get
    a full TelemetrySnapshot for context-aware reasoning.
    """

    def __init__(self, logger: Optional[RuntimeLogger] = None) -> None:
        self._logger = logger or RuntimeLogger()
        self._psutil: Any = None
        self._has_psutil = False
        self._boot_time: float = 0.0
        self._prev_net: Dict[str, int] = {}
        self._prev_net_time: float = 0.0
        self._initialised = False

    async def initialise(self) -> None:
        """Detect available telemetry backends."""
        self._has_psutil = await self._try_import_psutil()
        self._boot_time = self._get_boot_time()

        if self._has_psutil:
            self._logger.info("system_monitor", "psutil available — full telemetry")
        else:
            self._logger.info(
                "system_monitor",
                "psutil not installed — using /proc fallback (basic telemetry)",
            )

        self._initialised = True

    async def _try_import_psutil(self) -> bool:
        """Try importing psutil, return whether available."""
        try:
            import psutil as _ps

            self._psutil = _ps
            return True
        except ImportError:
            return False

    # ── Snapshot ──────────────────────────────────────────────────────────

    async def snapshot(self) -> TelemetrySnapshot:
        """Collect a full system telemetry snapshot."""
        if not self._initialised:
            await self.initialise()

        now = time.time()

        cpu = await self._get_cpu()
        memory = await self._get_memory()
        disk = await self._get_disk()
        network = await self._get_network(now)
        temperature = await self._get_temperature()

        hostname = platform.node()
        plat = platform.platform()
        uptime = now - self._boot_time if self._boot_time else 0.0
        processes = await self._get_process_count()
        services = await self._get_services()

        return TelemetrySnapshot(
            timestamp=now,
            cpu=cpu,
            memory=memory,
            disk=disk,
            network=network,
            temperature=temperature,
            hostname=hostname,
            platform=plat,
            uptime_seconds=uptime,
            boot_time=self._boot_time,
            processes=processes,
            services=services,
        )

    # ── CPU ───────────────────────────────────────────────────────────────

    async def _get_cpu(self) -> CpuInfo:
        info = CpuInfo()

        if self._has_psutil:
            info.percent = self._psutil.cpu_percent(interval=0.1)
            info.per_core = self._psutil.cpu_percent(interval=0.05, percpu=True)
            info.count_logical = self._psutil.cpu_count(logical=True) or 0
            info.count_physical = self._psutil.cpu_count(logical=False) or 0

            freq = self._psutil.cpu_freq()
            if freq:
                info.frequency_mhz = freq.current

            load = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
            info.load_avg_1m, info.load_avg_5m, info.load_avg_15m = load
        else:
            # Fallback: read /proc/stat
            info.count_logical = os.cpu_count() or 1
            info.count_physical = info.count_logical // 2 or 1
            try:
                with open("/proc/loadavg") as f:
                    parts = f.read().strip().split()
                    if len(parts) >= 3:
                        info.load_avg_1m = float(parts[0])
                        info.load_avg_5m = float(parts[1])
                        info.load_avg_15m = float(parts[2])
            except (FileNotFoundError, OSError, ValueError):
                pass
            info.percent = min(
                100.0, (info.load_avg_1m / info.count_logical) * 100.0
            )

        return info

    # ── Memory ────────────────────────────────────────────────────────────

    async def _get_memory(self) -> MemoryInfo:
        info = MemoryInfo()

        if self._has_psutil:
            mem = self._psutil.virtual_memory()
            info.total_gb = mem.total / (1024**3)
            info.used_gb = (mem.total - mem.available) / (1024**3)
            info.available_gb = mem.available / (1024**3)
            info.percent = mem.percent

            swap = self._psutil.swap_memory()
            info.swap_total_gb = swap.total / (1024**3)
            info.swap_used_gb = swap.used / (1024**3)
            info.swap_percent = swap.percent
        else:
            try:
                with open("/proc/meminfo") as f:
                    data = {}
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip().split()[0]
                            data[key] = int(val) * 1024  # kB → bytes

                total = data.get("MemTotal", 0)
                available = data.get("MemAvailable", 0)
                free = data.get("MemFree", 0)
                info.total_gb = total / (1024**3)
                info.available_gb = available / (1024**3)
                info.used_gb = (total - available) / (1024**3)
                info.percent = (
                    ((total - available) / total * 100) if total else 0
                )
            except (FileNotFoundError, OSError, KeyError):
                pass

        return info

    # ── Disk ──────────────────────────────────────────────────────────────

    async def _get_disk(self) -> DiskInfo:
        info = DiskInfo()

        if self._has_psutil:
            disk = self._psutil.disk_usage("/")
            info.total_gb = disk.total / (1024**3)
            info.used_gb = disk.used / (1024**3)
            info.free_gb = disk.free / (1024**3)
            info.percent = disk.percent
        else:
            try:
                stat = os.statvfs("/")
                total = stat.f_frsize * stat.f_blocks
                free = stat.f_frsize * stat.f_bfree
                info.total_gb = total / (1024**3)
                info.free_gb = free / (1024**3)
                info.used_gb = (total - free) / (1024**3)
                info.percent = (
                    ((total - free) / total * 100) if total else 0
                )
            except (AttributeError, OSError):
                pass

        return info

    # ── Network ───────────────────────────────────────────────────────────

    async def _get_network(self, now: float) -> NetworkInfo:
        info = NetworkInfo()

        if self._has_psutil:
            net = self._psutil.net_io_counters()
            info.bytes_sent_mb = net.bytes_sent / (1024**2)
            info.bytes_recv_mb = net.bytes_recv / (1024**2)
            info.packets_sent = net.packets_sent
            info.packets_recv = net.packets_recv

            # Connection count
            try:
                conns = self._psutil.net_connections()
                info.connections = len(conns)
            except (self._psutil.AccessDenied, PermissionError, OSError):
                info.connections = -1

            # Interface names
            addrs = self._psutil.net_if_addrs()
            info.interfaces = list(addrs.keys())
        else:
            try:
                with open("/proc/net/dev") as f:
                    for line in f:
                        if ":" in line:
                            parts = line.strip().split()
                            if len(parts) >= 10:
                                info.bytes_recv_mb += int(parts[1]) / (1024**2)
                                info.bytes_sent_mb += int(parts[9]) / (1024**2)
            except (FileNotFoundError, OSError, ValueError):
                pass

        return info

    # ── Temperature ───────────────────────────────────────────────────────

    async def _get_temperature(self) -> TemperatureInfo:
        info = TemperatureInfo()

        if self._has_psutil:
            try:
                temps = self._psutil.sensors_temperatures()
                # CPU temperatures (common labels)
                for key in ("coretemp", "cpu_thermal", "k10temp", "zenpower"):
                    if key in temps:
                        info.cpu_temp_c = temps[key][0].current
                        break
            except (AttributeError, OSError):
                pass

        # macOS fallback via sysctl
        if info.cpu_temp_c is None and platform.system() == "Darwin":
            try:
                proc = await asyncio.create_subprocess_exec(
                    "sysctl", "-n", "machdep.xcpm.cpu_thermal_level",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await proc.communicate()
                if stdout:
                    raw = stdout.decode().strip()
                    if raw:
                        info.cpu_temp_c = float(raw)
            except (FileNotFoundError, OSError, ValueError):
                pass

        if info.cpu_temp_c is None and platform.system() == "Darwin":
            try:
                proc = await asyncio.create_subprocess_exec(
                    "pmset", "-g", "therm",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await proc.communicate()
                if stdout:
                    raw = stdout.decode()
                    for line in raw.split("\n"):
                        if "CPU_Scheduler_Limit" in line:
                            # Not a direct temp but thermal throttle indicator
                            pass
            except (FileNotFoundError, OSError):
                pass

        return info

    # ── Process count ─────────────────────────────────────────────────────

    async def _get_process_count(self) -> int:
        if self._has_psutil:
            return len(self._psutil.pids())
        try:
            proc = await asyncio.create_subprocess_exec(
                "ps", "-e", "--no-headers",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()
            if stdout:
                return len(stdout.decode().strip().split("\n"))
        except (FileNotFoundError, OSError):
            pass
        return 0

    # ── Services ──────────────────────────────────────────────────────────

    async def _get_services(self) -> List[ServiceInfo]:
        """Collect running services relevant to AXIOM OS."""
        services: List[ServiceInfo] = []
        self._add_axiom_process(services)

        if self._has_psutil:
            for proc in self._psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_info", "create_time"]
            ):
                try:
                    pinfo = proc.info
                    services.append(
                        ServiceInfo(
                            name=pinfo["name"] or "unknown",
                            status="running",
                            pid=pinfo["pid"],
                            cpu_percent=pinfo["cpu_percent"] or 0.0,
                            memory_mb=(
                                (pinfo["memory_info"].rss / (1024**2))
                                if pinfo["memory_info"]
                                else 0.0
                            ),
                            uptime_seconds=(
                                time.time() - (pinfo["create_time"] or time.time())
                            ),
                        )
                    )
                except (self._psutil.NoSuchProcess, AttributeError):
                    continue

        return services[:50]  # Cap at 50

    def _add_axiom_process(self, services: List[ServiceInfo]) -> None:
        """Add the current AXIOM process to the service list."""
        try:
            import os as _os

            pid = _os.getpid()
            services.append(
                ServiceInfo(
                    name="axiom-backend",
                    status="running",
                    pid=pid,
                    uptime_seconds=time.time() - self._boot_time,
                )
            )
        except Exception:
            pass

    # ── Boot time ─────────────────────────────────────────────────────────

    def _get_boot_time(self) -> float:
        if self._has_psutil:
            try:
                return self._psutil.boot_time()
            except Exception:
                pass

        try:
            with open("/proc/stat") as f:
                for line in f:
                    if line.startswith("btime"):
                        return float(line.strip().split()[1])
        except (FileNotFoundError, OSError, ValueError):
            pass

        # Fallback: current time - uptime from sysctl
        if platform.system() == "Darwin":
            try:
                import subprocess

                result = subprocess.run(
                    ["sysctl", "-n", "kern.boottime"],
                    capture_output=True, text=True,
                )
                if result.returncode == 0:
                    # Parse: { sec = 12345, usec = 0 }
                    import re

                    match = re.search(r"sec\s*=\s*(\d+)", result.stdout)
                    if match:
                        return float(match.group(1))
            except (FileNotFoundError, OSError):
                pass

        return time.time()

    # ── Network Check ────────────────────────────────────────────────────

    async def check_connectivity(self, host: str = "8.8.8.8") -> bool:
        """Check basic network connectivity by pinging a host."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "2", host,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            ret = await proc.wait()
            return ret == 0
        except (FileNotFoundError, OSError):
            return False

    # ── Utility ──────────────────────────────────────────────────────────

    def format_summary(self, snapshot: TelemetrySnapshot) -> str:
        """Return a human-readable one-line system summary."""
        return (
            f"CPU {snapshot.cpu.percent:.0f}% | "
            f"RAM {snapshot.memory.percent:.0f}% ({snapshot.memory.used_gb:.1f}/{snapshot.memory.total_gb:.1f} GB) | "
            f"Disk {snapshot.disk.percent:.0f}% | "
            f"Health: {snapshot.health_label.upper()}"
        )

    async def health_check(self) -> Dict[str, Any]:
        """Quick health check for the monitor endpoint."""
        snap = await self.snapshot()
        return {
            "healthy": snap.health_score >= 0.5,
            "health_score": snap.health_score,
            "health_label": snap.health_label,
            "cpu_percent": snap.cpu.percent,
            "memory_percent": snap.memory.percent,
            "disk_percent": snap.disk.percent,
            "uptime_seconds": snap.uptime_seconds,
            "processes": snap.processes,
            "hostname": snap.hostname,
            "platform": snap.platform,
        }

    async def shutdown(self) -> None:
        """Graceful shutdown — release resources."""
        self._initialised = False
        if self._logger:
            self._logger.info("system_monitor", "System Monitor shut down")