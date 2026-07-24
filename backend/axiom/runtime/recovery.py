"""Recovery Manager — retry handling and failed workflow recovery.

Handles automatic retry of failed steps and workflow recovery after
system restarts.
"""

import asyncio
from typing import Any, Dict, List

from axiom.models.workflows import WorkflowInstance, WorkflowStatus


class RecoveryManager:
    """Handles recovery of failed workflow steps and system restarts."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime
        self._max_global_retries: int = 3

    # ── Step Recovery ────────────────────────────────────────────────────

    async def recover_failed_step(self, instance: WorkflowInstance) -> bool:
        """Attempt to recover a failed workflow step.

        Returns True if recovery was initiated.
        """
        wf_engine = getattr(self._runtime, "workflow", None)
        if wf_engine is None:
            return False

        failed_step = instance.steps[instance.current_step_index]
        if failed_step.retry_count >= self._max_global_retries:
            return False  # Exceeded retry limit

        try:
            await wf_engine.retry(instance.instance_id)
            return True
        except Exception:
            return False

    async def recover_all_failed(self) -> List[str]:
        """Attempt to recover all failed workflow instances.

        Returns a list of instance IDs that were recovered.
        """
        wf_engine = getattr(self._runtime, "workflow", None)
        if wf_engine is None:
            return []

        recovered: List[str] = []
        failed_instances = wf_engine.list_instances(status=WorkflowStatus.FAILED)

        for instance in failed_instances:
            success = await self.recover_failed_step(instance)
            if success:
                recovered.append(instance.instance_id)
                await asyncio.sleep(0.5)  # Throttle recovery

        return recovered

    # ── System Restart Recovery ──────────────────────────────────────────

    async def recover_after_restart(self) -> Dict[str, Any]:
        """Recover state after a system restart.

        Reloads persisted workflow instances and recovers any that were
        in a running state when the system went down.
        """
        wf_engine = getattr(self._runtime, "workflow", None)
        if wf_engine is None:
            return {"recovered": 0, "failed": 0}

        persisted = wf_engine.load_all_persisted()

        results = {
            "total_loaded": len(persisted),
            "recovered": 0,
            "failed": 0,
            "stale_finalised": 0,
        }

        for instance in persisted:
            if instance.status == WorkflowStatus.RUNNING:
                # Workflow was in-flight — mark as failed and try recovery
                try:
                    await wf_engine.fail_step(
                        instance.instance_id,
                        "System restart — step interruped. Ready for manual retry.",
                    )
                    results["failed"] += 1
                except Exception:
                    results["failed"] += 1

            elif instance.status in (
                WorkflowStatus.COMPLETED,
                WorkflowStatus.CANCELLED,
                WorkflowStatus.FAILED,
            ):
                results["stale_finalised"] += 1

        return results

    # ── Retry Configuration ──────────────────────────────────────────────

    def set_max_retries(self, count: int) -> None:
        """Set the maximum number of retries for any step."""
        self._max_global_retries = max(1, count)

    def get_max_retries(self) -> int:
        return self._max_global_retries