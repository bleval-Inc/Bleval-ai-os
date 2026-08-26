"""Resource Monitor — CPU, memory, disk, network, GPU monitoring."""

import asyncio
import os
import psutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable

from pydantic import BaseModel, Field

from axiom.runtime.logging import RuntimeLogger


class ResourceMetrics(BaseModel):
    """Current resource metrics."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # CPU
    cpu_percent: float = 0.0
    cpu_per_core: List[float] = Field(default_factory=list)
    cpu_count: int = 0
    load_avg: List[float] = Field(default_factory=list)

    # Memory
    memory_total: int = 0
    memory_available: int = 0
    memory_used: int = 0
    memory_percent: float = 0.0
    swap_total: int = 0
    swap_used: int = 0
    swap_percent: float = 0.0

    # Disk
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0
    disk_percent: float = 0.0
    disk_io_read: int = 0
    disk_io_write: int = 0

    # Network
    net_bytes_sent: int = 0
    net_bytes_recv: int = 0
    net_packets_sent: int = 0
    net_packets_recv: int = 0

    # Process
    process_count: int = 0
    thread_count: int = 0
    open_files: int = 0

    # GPU (if available)
    gpu_available: bool = False
    gpu_devices: List[Dict[str, Any]] = Field(default_factory=list)

    # Custom
    custom_metrics: Dict[str, float] = Field(default_factory=dict)


class ResourceAlert(BaseModel):
    """Resource alert."""

    level: str  # info, warning, critical
    resource: str  # cpu, memory, disk, gpu, custom
    message: str
    value: float
    threshold: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False


class AlertRule(BaseModel):
    """Alert rule configuration."""

    name: str
    resource: str
    condition: str  # "gt", "lt", "gte", "lte"
    threshold: float
    level: str = "warning"
    cooldown_seconds: int = 300
    enabled: bool = True


class ResourceMonitor:
    """Monitors system resources."""

    def __init__(
        self,
        interval_seconds: int = 30,
        alert_rules: Optional[List[AlertRule]] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.interval = interval_seconds
        self.alert_rules = alert_rules or self._default_rules()
        self.logger = logger or RuntimeLogger()

        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._history: List[ResourceMetrics] = []
        self._max_history = 1000
        self._alerts: List[ResourceAlert] = []
        self._last_alert: Dict[str, datetime] = {}
        self._callbacks: List[Callable[[ResourceAlert], Any]] = []
        self._process = psutil.Process()
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()

    def _default_rules(self) -> List[AlertRule]:
        return [
            AlertRule(name="high_cpu", resource="cpu_percent", condition="gt", threshold=85, level="warning"),
            AlertRule(name="critical_cpu", resource="cpu_percent", condition="gt", threshold=95, level="critical"),
            AlertRule(name="high_memory", resource="memory_percent", condition="gt", threshold=85, level="warning"),
            AlertRule(name="critical_memory", resource="memory_percent", condition="gt", threshold=95, level="critical"),
            AlertRule(name="high_disk", resource="disk_percent", condition="gt", threshold=90, level="warning"),
            AlertRule(name="critical_disk", resource="disk_percent", condition="gt", threshold=98, level="critical"),
            AlertRule(name="high_swap", resource="swap_percent", condition="gt", threshold=50, level="warning"),
        ]

    def add_callback(self, callback: Callable[[ResourceAlert], Any]):
        """Add alert callback."""
        self._callbacks.append(callback)

    def add_rule(self, rule: AlertRule):
        """Add custom alert rule."""
        self.alert_rules.append(rule)

    async def start(self):
        """Start monitoring."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        self.logger.info("resource_monitor", "Resource monitor started")

    async def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("resource_monitor", "Resource monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                metrics = await self.collect_metrics()
                self._history.append(metrics)
                if len(self._history) > self._max_history:
                    self._history.pop(0)

                self._check_alerts(metrics)
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("resource_monitor", f"Monitor loop error: {e}")
                await asyncio.sleep(5)

    async def collect_metrics(self) -> ResourceMetrics:
        """Collect current metrics."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_count = psutil.cpu_count()
        load_avg = list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else [0, 0, 0]

        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk
        disk = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()
        disk_read = disk_io.read_bytes - self._last_disk_io.read_bytes if self._last_disk_io else 0
        disk_write = disk_io.write_bytes - self._last_disk_io.write_bytes if self._last_disk_io else 0
        self._last_disk_io = disk_io

        # Network
        net_io = psutil.net_io_counters()
        net_sent = net_io.bytes_sent - self._last_net_io.bytes_sent if self._last_net_io else 0
        net_recv = net_io.bytes_recv - self._last_net_io.bytes_recv if self._last_net_io else 0
        net_psent = net_io.packets_sent - self._last_net_io.packets_sent if self._last_net_io else 0
        net_precv = net_io.packets_recv - self._last_net_io.packets_recv if self._last_net_io else 0
        self._last_net_io = net_io

        # Process
        try:
            proc_count = len(psutil.pids())
            thread_count = self._process.num_threads()
            open_files = len(self._process.open_files())
        except Exception:
            proc_count = 0
            thread_count = 0
            open_files = 0

        # GPU
        gpu_available = False
        gpu_devices = []
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_available = True
                for gpu in gpus:
                    gpu_devices.append({
                        "id": gpu.id,
                        "name": gpu.name,
                        "load": gpu.load * 100,
                        "memory_used": gpu.memoryUsed,
                        "memory_total": gpu.memoryTotal,
                        "memory_percent": gpu.memoryUtil * 100,
                        "temperature": gpu.temperature,
                    })
        except ImportError:
            pass

        return ResourceMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            cpu_per_core=cpu_per_core,
            cpu_count=cpu_count,
            load_avg=load_avg,
            memory_total=mem.total,
            memory_available=mem.available,
            memory_used=mem.used,
            memory_percent=mem.percent,
            swap_total=swap.total,
            swap_used=swap.used,
            swap_percent=swap.percent,
            disk_total=disk.total,
            disk_used=disk.used,
            disk_free=disk.free,
            disk_percent=disk.percent,
            disk_io_read=disk_read,
            disk_io_write=disk_write,
            net_bytes_sent=net_sent,
            net_bytes_recv=net_recv,
            net_packets_sent=net_psent,
            net_packets_recv=net_precv,
            process_count=proc_count,
            thread_count=thread_count,
            open_files=open_files,
            gpu_available=gpu_available,
            gpu_devices=gpu_devices,
        )

    def _check_alerts(self, metrics: ResourceMetrics):
        """Check alert rules against metrics."""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            value = getattr(metrics, rule.resource, None)
            if value is None:
                continue

            triggered = False
            if rule.condition == "gt" and value > rule.threshold:
                triggered = True
            elif rule.condition == "gte" and value >= rule.threshold:
                triggered = True
            elif rule.condition == "lt" and value < rule.threshold:
                triggered = True
            elif rule.condition == "lte" and value <= rule.threshold:
                triggered = True

            if triggered:
                # Check cooldown
                key = f"{rule.name}_{rule.resource}_{rule.condition}_{rule.threshold}"
                last = self._last_alert.get(key)
                if last and (datetime.utcnow() - last).total_seconds() < rule.cooldown_seconds:
                    continue

                alert = ResourceAlert(
                    level=rule.level,
                    resource=rule.resource,
                    message=f"{rule.name}: {rule.resource} {rule.condition} {rule.threshold} (current: {value:.1f})",
                    value=value,
                    threshold=rule.threshold,
                )

                self._alerts.append(alert)
                self._last_alert[key] = datetime.utcnow()

                # Trigger callbacks
                for callback in self._callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            asyncio.create_task(callback(alert))
                        else:
                            callback(alert)
                    except Exception as e:
                        self.logger.error("resource_monitor", f"Alert callback error: {e}")

    def get_current(self) -> Optional[ResourceMetrics]:
        """Get latest metrics."""
        return self._history[-1] if self._history else None

    def get_history(
        self,
        duration: Optional[timedelta] = None,
        max_points: int = 100,
    ) -> List[ResourceMetrics]:
        """Get metrics history."""
        if not self._history:
            return []

        if duration:
            cutoff = datetime.utcnow() - duration
            filtered = [m for m in self._history if m.timestamp >= cutoff]
        else:
            filtered = self._history

        # Downsample if too many points
        if len(filtered) > max_points:
            step = len(filtered) // max_points + 1
            filtered = filtered[::step]

        return filtered

    def get_alerts(
        self,
        unacknowledged_only: bool = False,
        since: Optional[datetime] = None,
    ) -> List[ResourceAlert]:
        """Get alerts."""
        alerts = self._alerts
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]
        return alerts

    def acknowledge_alert(self, alert: ResourceAlert):
        """Acknowledge an alert."""
        alert.acknowledged = True

    def get_averages(self, duration: timedelta) -> Dict[str, float]:
        """Get average metrics over duration."""
        history = self.get_history(duration)
        if not history:
            return {}

        return {
            "cpu_percent": sum(m.cpu_percent for m in history) / len(history),
            "memory_percent": sum(m.memory_percent for m in history) / len(history),
            "disk_percent": sum(m.disk_percent for m in history) / len(history),
            "load_avg_1m": sum(m.load_avg[0] for m in history) / len(history) if history[0].load_avg else 0,
        }

    def get_peak_usage(self, duration: timedelta) -> Dict[str, float]:
        """Get peak usage over duration."""
        history = self.get_history(duration)
        if not history:
            return {}

        return {
            "cpu_percent": max(m.cpu_percent for m in history),
            "memory_percent": max(m.memory_percent for m in history),
            "disk_percent": max(m.disk_percent for m in history),
        }

    async def get_process_metrics(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get metrics for specific process."""
        try:
            proc = psutil.Process(pid)
            return {
                "pid": pid,
                "name": proc.name(),
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "memory_percent": proc.memory_percent(),
                "memory_mb": proc.memory_info().rss / 1024 / 1024,
                "threads": proc.num_threads(),
                "open_files": len(proc.open_files()),
                "connections": len(proc.connections()),
                "create_time": datetime.fromtimestamp(proc.create_time()),
            }
        except psutil.NoSuchProcess:
            return None