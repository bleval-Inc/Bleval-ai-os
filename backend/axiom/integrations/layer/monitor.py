"""Integration Monitor — Comprehensive monitoring and health tracking."""

import asyncio
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from axiom.runtime.logging import RuntimeLogger

from .models import MonitoringConfig


class IntegrationMonitor:
    """Monitors integration health, performance, and data quality."""

    def __init__(
        self,
        config: MonitoringConfig,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.config = config
        self.logger = logger or RuntimeLogger()

        # Metrics storage (in-memory, rolling windows)
        self._latency_samples: deque = deque(maxlen=1000)
        self._throughput_samples: deque = deque(maxlen=1000)
        self._error_samples: deque = deque(maxlen=1000)
        self._quality_samples: deque = deque(maxlen=1000)

        # Cycle history
        self._cycle_history: List[Dict[str, Any]] = []
        self._max_history = 100

        # Health check
        self._health_check_task: Optional[asyncio.Task] = None
        self._last_health_check: Optional[datetime] = None

        # Alerting
        self._alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []

    async def start(self) -> None:
        """Start background health checks."""
        if self.config.enabled and self.config.health_check_interval_seconds > 0:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """Stop background health checks."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

    def register_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Register a callback for alerts."""
        self._alert_callbacks.append(callback)

    async def record_cycle(self, metrics: Dict[str, Any]) -> None:
        """Record metrics from an integration cycle."""
        timestamp = datetime.utcnow()

        # Latency
        if self.config.collect_latency:
            total_duration = metrics.get("total_duration_ms", 0)
            self._latency_samples.append({"timestamp": timestamp, "value": total_duration})

        # Throughput
        if self.config.collect_throughput:
            fetched = metrics.get("fetched_count", 0)
            duration = metrics.get("total_duration_ms", 1)
            throughput = (fetched / duration * 1000) if duration > 0 else 0  # records/second
            self._throughput_samples.append({"timestamp": timestamp, "value": throughput})

        # Error rate
        if self.config.collect_error_rates:
            error_count = metrics.get("error_count", 0)
            total_count = metrics.get("fetched_count", 1)
            error_rate = error_count / total_count if total_count > 0 else 0
            self._error_samples.append({"timestamp": timestamp, "value": error_rate})

        # Data quality
        if self.config.collect_data_quality:
            validated = metrics.get("validated_count", 0)
            fetched = metrics.get("fetched_count", 1)
            quality = validated / fetched if fetched > 0 else 0
            self._quality_samples.append({"timestamp": timestamp, "value": quality})

        # Custom metrics
        for metric_fn in self.config.custom_metrics:
            try:
                custom = metric_fn(metrics)
                for name, value in custom.items():
                    if not hasattr(self, f"_{name}_samples"):
                        setattr(self, f"_{name}_samples", deque(maxlen=1000))
                    getattr(self, f"_{name}_samples").append({"timestamp": timestamp, "value": value})
            except Exception as e:
                self.logger.warning(f"Custom metric failed: {e}")

        # Store cycle summary
        self._cycle_history.append({
            "timestamp": timestamp,
            "metrics": metrics,
        })
        if len(self._cycle_history) > self._max_history:
            self._cycle_history.pop(0)

        # Check alerts
        await self._check_alerts(metrics)

    async def _check_alerts(self, metrics: Dict[str, Any]) -> None:
        """Check if any alert thresholds are breached."""
        error_count = metrics.get("error_count", 0)
        total_count = metrics.get("fetched_count", 1)
        error_rate = error_count / total_count if total_count > 0 else 0

        total_duration = metrics.get("total_duration_ms", 0)

        alerts = []

        if self.config.alert_on_failure and error_count > 0:
            alerts.append({
                "type": "failure",
                "severity": "high",
                "message": f"Integration cycle had {error_count} errors",
                "metrics": {"error_count": error_count},
            })

        if self.config.alert_on_rate_limited and metrics.get("rate_limited", False):
            alerts.append({
                "type": "rate_limited",
                "severity": "medium",
                "message": "Integration was rate limited",
                "metrics": {},
            })

        if error_rate > self.config.alert_threshold_error_rate:
            alerts.append({
                "type": "high_error_rate",
                "severity": "high",
                "message": f"Error rate {error_rate:.2%} exceeds threshold {self.config.alert_threshold_error_rate:.2%}",
                "metrics": {"error_rate": error_rate},
            })

        if total_duration > self.config.alert_threshold_latency_p99_ms:
            alerts.append({
                "type": "high_latency",
                "severity": "medium",
                "message": f"Cycle latency {total_duration:.0f}ms exceeds threshold {self.config.alert_threshold_latency_p99_ms:.0f}ms",
                "metrics": {"latency_ms": total_duration},
            })

        # Fire alerts
        for alert in alerts:
            await self._fire_alert(alert)

    async def _fire_alert(self, alert: Dict[str, Any]) -> None:
        """Fire an alert to all registered callbacks."""
        for callback in self._alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert["type"], alert)
                else:
                    callback(alert["type"], alert)
            except Exception as e:
                self.logger.warning(f"Alert callback failed: {e}")

        self.logger.warning(f"ALERT [{alert['severity'].upper()}]: {alert['message']}")

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval_seconds)
                await self._run_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.warning(f"Health check error: {e}")

    async def _run_health_check(self) -> None:
        """Run a health check."""
        self._last_health_check = datetime.utcnow()

        # Calculate health metrics
        health = self.get_health_summary()

        # Log health status
        self.logger.debug(
            f"Integration health: score={health['health_score']:.2f}, "
            f"latency_p50={health.get('latency_p50_ms', 0):.0f}ms, "
            f"error_rate={health.get('error_rate', 0):.2%}"
        )

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        now = datetime.utcnow()
        window = timedelta(minutes=5)

        # Filter recent samples
        recent_latency = [
            s["value"] for s in self._latency_samples
            if now - s["timestamp"] < window
        ]
        recent_errors = [
            s["value"] for s in self._error_samples
            if now - s["timestamp"] < window
        ]
        recent_quality = [
            s["value"] for s in self._quality_samples
            if now - s["timestamp"] < window
        ]
        recent_throughput = [
            s["value"] for s in self._throughput_samples
            if now - s["timestamp"] < window
        ]

        # Percentiles
        def percentile(values: List[float], p: float) -> float:
            if not values:
                return 0.0
            sorted_vals = sorted(values)
            idx = int(len(sorted_vals) * p)
            return sorted_vals[min(idx, len(sorted_vals) - 1)]

        return {
            "health_score": self._calculate_health_score(),
            "last_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "latency_p50_ms": percentile(recent_latency, 0.5),
            "latency_p95_ms": percentile(recent_latency, 0.95),
            "latency_p99_ms": percentile(recent_latency, 0.99),
            "avg_latency_ms": sum(recent_latency) / len(recent_latency) if recent_latency else 0,
            "error_rate": sum(recent_errors) / len(recent_errors) if recent_errors else 0,
            "data_quality": sum(recent_quality) / len(recent_quality) if recent_quality else 0,
            "throughput_rps": sum(recent_throughput) / len(recent_throughput) if recent_throughput else 0,
            "cycle_count_5m": len(recent_latency),
            "total_cycles": len(self._cycle_history),
        }

    def _calculate_health_score(self) -> float:
        """Calculate overall health score (0-1)."""
        if not self._cycle_history:
            return 1.0

        # Recent cycles (last 10)
        recent = self._cycle_history[-10:]

        scores = []
        for cycle in recent:
            metrics = cycle.get("metrics", {})
            error_count = metrics.get("error_count", 0)
            fetched = metrics.get("fetched_count", 1)
            error_rate = error_count / fetched if fetched > 0 else 0

            # Score based on error rate (lower is better)
            cycle_score = max(0.0, 1.0 - error_rate * 2)
            scores.append(cycle_score)

        return sum(scores) / len(scores) if scores else 1.0

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get detailed metrics summary."""
        return {
            "latency": self._calculate_percentiles(self._latency_samples),
            "throughput": self._calculate_percentiles(self._throughput_samples),
            "error_rate": self._calculate_percentiles(self._error_samples),
            "data_quality": self._calculate_percentiles(self._quality_samples),
            "recent_cycles": self._cycle_history[-10:],
        }

    def _calculate_percentiles(self, samples: deque) -> Dict[str, float]:
        """Calculate percentiles for a sample set."""
        values = [s["value"] for s in samples]
        if not values:
            return {"p50": 0, "p95": 0, "p99": 0, "avg": 0, "count": 0}

        sorted_vals = sorted(values)
        return {
            "p50": sorted_vals[int(len(sorted_vals) * 0.5)],
            "p95": sorted_vals[int(len(sorted_vals) * 0.95)],
            "p99": sorted_vals[int(len(sorted_vals) * 0.99)],
            "avg": sum(values) / len(values),
            "count": len(values),
        }

    def get_recent_cycles(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent cycle history."""
        return self._cycle_history[-count:]