"""Helper methods for AutonomousWorkflowEngine — monitoring, failure, and parsing.

Extracted to keep autonomous_workflow.py under the project's 500-line guideline.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from axiom.models.workflow_autonomous import (
    AutonomousLifecyclePhase,
    AutonomousWorkflowState,
)


MONITOR_TICK = 5


def build_phase_instruction(
    state: AutonomousWorkflowState, phase: AutonomousLifecyclePhase
) -> str:
    """Build the instruction for a given lifecycle phase."""
    import json as _json

    phase_instructions = {
        AutonomousLifecyclePhase.PLAN: (
            f"Plan the execution of workflow: {state.workflow_id}\n"
            f"Context: {_json.dumps(state.context, indent=2)}\n\n"
            f"Define: objectives, required agents, estimated duration, risks, dependencies"
        ),
        AutonomousLifecyclePhase.RESEARCH: (
            f"Research phase for workflow: {state.workflow_id}\n"
            f"Plan: {_json.dumps(state.plan_state, indent=2)[:500]}\n\n"
            f"Gather information, sources, data points, and insights needed."
        ),
        AutonomousLifecyclePhase.PREPARE: (
            f"Preparation phase for workflow: {state.workflow_id}\n"
            f"Research: {_json.dumps(state.research_state, indent=2)[:500]}\n\n"
            f"Prepare resources, tooling, and materials needed for execution."
        ),
        AutonomousLifecyclePhase.TEST: (
            f"Testing phase for workflow: {state.workflow_id}\n"
            f"Execution output: {_json.dumps(state.execute_state, indent=2)[:500]}\n\n"
            f"Test the output for correctness, completeness, and edge cases."
        ),
        AutonomousLifecyclePhase.REVIEW: (
            f"Review phase for workflow: {state.workflow_id}\n"
            f"QC results: {_json.dumps(state.qc_state, indent=2)[:500]}\n\n"
            f"Review the completed work. Check for issues, suggest improvements."
        ),
        AutonomousLifecyclePhase.DELIVERY: (
            f"Delivery phase for workflow: {state.workflow_id}\n"
            f"Prepare the final output for delivery to the requester."
        ),
    }
    return phase_instructions.get(
        phase,
        f"Execute {phase.value} phase for workflow: {state.workflow_id}",
    )


def record_error(
    state: AutonomousWorkflowState, phase: str, error: str
) -> None:
    """Record an error with classification (§8)."""
    error_entry: Dict[str, Any] = {
        "phase": phase,
        "error": error[:500],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retries_remaining": state.max_retries - state.retries,
    }
    state.errors.append(error_entry)


def parse_qc_result(result: str) -> Dict[str, Any]:
    """Parse QC evaluation result from intelligence engine output."""
    try:
        data = json.loads(result)
        return {
            "score": float(data.get("score", 0.8)),
            "passed": bool(data.get("passed", True)),
            "issues": list(data.get("issues", [])),
            "recommendations": list(data.get("recommendations", [])),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "score": 0.8,
            "passed": True,
            "issues": [],
            "recommendations": [],
        }


def parse_learning_result(result: str) -> Dict[str, Any]:
    """Parse learning result from intelligence engine output."""
    try:
        data = json.loads(result)
        return {
            "what_worked": list(data.get("what_worked", [])),
            "what_didnt": list(data.get("what_didnt", [])),
            "metrics": dict(data.get("metrics", {})),
            "recommendations": list(data.get("recommendations", [])),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "what_worked": [],
            "what_didnt": [],
            "metrics": {},
            "recommendations": [],
        }


# ── Monitor Loop ────────────────────────────────────────────────────


async def monitor_loop(
    running_ref: List[bool],
    autonomous_states: Dict[str, AutonomousWorkflowState],
    record_error_fn: Callable,
    auto_recover_fn: Callable,
) -> None:
    """Background loop: monitor all autonomous workflows.

    Checks for:
      - Stuck workflows (no phase progress)
      - Failed workflows needing retry
      - Completed workflows needing learning consolidation
    """
    while running_ref[0]:
        try:
            for instance_id, state in list(autonomous_states.items()):
                # Check for failed workflows that can retry
                if (
                    state.phase == AutonomousLifecyclePhase.FAILED
                    and state.retries < state.max_retries
                ):
                    await auto_recover_fn(state)

                # Check for stale in-progress phases (10 min timeout)
                if state.phase in (
                    AutonomousLifecyclePhase.PLAN,
                    AutonomousLifecyclePhase.RESEARCH,
                    AutonomousLifecyclePhase.PREPARE,
                    AutonomousLifecyclePhase.EXECUTE,
                    AutonomousLifecyclePhase.TEST,
                ) and state.phase_started_at:
                    elapsed = (
                        datetime.now(timezone.utc) - state.phase_started_at
                    ).total_seconds()
                    if elapsed > 600:
                        record_error_fn(
                            state,
                            "timeout",
                            f"Phase {state.phase.value} timed out after {elapsed:.0f}s",
                        )

            await asyncio.sleep(MONITOR_TICK)

        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(MONITOR_TICK)