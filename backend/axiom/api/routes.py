"""FastAPI route definitions for Axiom OS.

Exposes the runtime capabilities via REST API.
Uses public engine methods — never accesses private attributes.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axiom.models.workflows import ApprovalStatus, WorkflowStatus

# Router — mounted in main.py
router = APIRouter(prefix="/api/v1")

# In-memory reference to the runtime (set during app startup)
_runtime = None


def set_runtime(runtime: Any) -> None:
    """Inject runtime reference into the API layer."""
    global _runtime
    _runtime = runtime


def _get_runtime():
    if _runtime is None:
        raise HTTPException(status_code=503, detail="Runtime not initialised")
    return _runtime


# ── Request/Response models ─────────────────────────────────────────────

class WorkflowLaunchRequest(BaseModel):
    workflow_id: str
    context: Dict[str, Any] = {}


class WorkflowLaunchResponse(BaseModel):
    instance_id: str
    workflow_id: str
    status: str


class ApprovalResponse(BaseModel):
    approval_id: str
    approved: bool
    approved_by: str
    notes: Optional[str] = None


# ── System Routes ───────────────────────────────────────────────────────

@router.get("/status")
async def get_status():
    """Return runtime status."""
    rt = _get_runtime()
    return rt.get_summary()


@router.get("/health")
async def get_health():
    """Return health summary of all components."""
    rt = _get_runtime()
    if rt.monitor:
        return rt.monitor.get_summary()
    return {"error": "Monitor not available"}


# ── Organisation Routes ─────────────────────────────────────────────────

@router.get("/organisations")
async def list_organisations():
    """List all registered organisations."""
    rt = _get_runtime()
    if rt.executive:
        return [{"id": o.id, "name": o.name, "executives": o.executives}
                for o in rt.executive.list_organizations()]
    return []


@router.get("/organisations/{org_id}")
async def get_organisation(org_id: str):
    """Get organisation details."""
    rt = _get_runtime()
    if rt.executive:
        detail = rt.executive.get_organization_detail(org_id)
        if detail:
            return detail
    raise HTTPException(status_code=404, detail=f"Organisation {org_id} not found")


# ── Executive Routes ────────────────────────────────────────────────────

@router.get("/executives")
async def list_executives():
    """List all executive agents."""
    rt = _get_runtime()
    if rt.executive:
        return [{"id": e.id, "org": e.org, "department": e.department}
                for e in rt.executive.list_executives()]
    return []


@router.get("/executives/{exec_id}")
async def get_executive(exec_id: str):
    """Get executive details."""
    rt = _get_runtime()
    if rt.executive:
        detail = rt.executive.get_executive_detail(exec_id)
        if detail:
            return detail
    raise HTTPException(status_code=404, detail=f"Executive {exec_id} not found")


# ── Executive Board Routes ──────────────────────────────────────────────


@router.get("/executives/board/status")
async def get_executive_board_status():
    """Get status of all executive runtime loops."""
    rt = _get_runtime()
    if rt.executive_board:
        return rt.executive_board.get_status()
    return {"error": "Executive Board not available"}


@router.post("/executives/board/trigger")
async def trigger_executive_board(cycle_type: str = "manual"):
    """Trigger a cycle for all executives (testing / ad-hoc)."""
    rt = _get_runtime()
    if rt.executive_board:
        results = await rt.executive_board.trigger_all(cycle_type)
        return results
    raise HTTPException(status_code=503, detail="Executive Board not available")


@router.get("/executives/{exec_id}/loop/status")
async def get_executive_loop_status(exec_id: str):
    """Get the runtime loop status for a specific executive."""
    rt = _get_runtime()
    if rt.executive_board:
        loop = rt.executive_board.get_loop(exec_id)
        if loop:
            return loop.get_status()
        raise HTTPException(status_code=404, detail=f"Executive {exec_id} not found")
    raise HTTPException(status_code=503, detail="Executive Board not available")


@router.post("/executives/{exec_id}/loop/trigger")
async def trigger_executive_cycle(exec_id: str, cycle_type: str = "manual"):
    """Manually trigger a runtime cycle for a specific executive."""
    rt = _get_runtime()
    if rt.executive_board:
        loop = rt.executive_board.get_loop(exec_id)
        if loop:
            result = await loop.trigger_cycle(cycle_type)
            return result
        raise HTTPException(status_code=404, detail=f"Executive {exec_id} not found")
    raise HTTPException(status_code=503, detail="Executive Board not available")


@router.get("/executives/{exec_id}/loop/schedules")
async def get_executive_schedules(exec_id: str):
    """Get the configured schedules for an executive's runtime loop."""
    rt = _get_runtime()
    if rt.executive_board:
        loop = rt.executive_board.get_loop(exec_id)
        if loop:
            return loop.list_schedules()
        raise HTTPException(status_code=404, detail=f"Executive {exec_id} not found")
    raise HTTPException(status_code=503, detail="Executive Board not available")


@router.post("/executives/{exec_id}/loop/schedules")
async def set_executive_schedule(
    exec_id: str,
    name: str,
    cron: str,
    description: str = "",
):
    """Set a schedule for an executive's runtime loop."""
    rt = _get_runtime()
    if rt.executive_board:
        loop = rt.executive_board.get_loop(exec_id)
        if loop:
            loop.set_schedule(name, cron, description)
            return {"exec_id": exec_id, "schedule": name, "cron": cron}
        raise HTTPException(status_code=404, detail=f"Executive {exec_id} not found")
    raise HTTPException(status_code=503, detail="Executive Board not available")


# ── Department Routes ───────────────────────────────────────────────────

@router.get("/organisations/{org_id}/departments")
async def list_departments(org_id: str):
    """List departments in an organisation."""
    rt = _get_runtime()
    if rt.executive:
        return rt.executive.get_departments(org_id)
    return []


# ── Agent Routes ────────────────────────────────────────────────────────

@router.get("/agents")
async def list_agents():
    """List all registered agents."""
    rt = _get_runtime()
    if rt.executive:
        return [{"id": a.id, "org": a.org, "department": a.department, "type": a.type}
                for a in rt.executive.list_all_agents()]
    return []


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details."""
    rt = _get_runtime()
    if rt.executive:
        detail = rt.executive.get_agent_detail(agent_id)
        if detail:
            return detail
    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")


# ── Workflow Routes ─────────────────────────────────────────────────────

@router.get("/workflows")
async def list_workflows():
    """List all defined workflows."""
    rt = _get_runtime()
    if rt.workflow:
        return [{"id": wf_id, "description": wf.description, "department": wf.department,
                 "org": wf.org, "steps": len(wf.steps)}
                for wf_id, wf in rt.workflow.list_workflows().items()]
    return []


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow definition."""
    rt = _get_runtime()
    if rt.workflow:
        wf = rt.workflow.get_workflow(workflow_id)
        if wf:
            return wf
    raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")


@router.post("/workflows/launch", response_model=WorkflowLaunchResponse)
async def launch_workflow(request: WorkflowLaunchRequest):
    """Launch a workflow instance."""
    rt = _get_runtime()
    if not rt.workflow:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        instance = rt.workflow.create_instance(request.workflow_id, request.context)
        await rt.workflow.start(instance.instance_id)
        return WorkflowLaunchResponse(
            instance_id=instance.instance_id,
            workflow_id=instance.workflow_id,
            status=instance.status.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Workflow Instance Routes ────────────────────────────────────────────

@router.get("/instances")
async def list_instances(status: Optional[str] = None):
    """List workflow instances, optionally filtered by status."""
    rt = _get_runtime()
    if not rt.workflow:
        return []
    status_filter = WorkflowStatus(status) if status else None
    instances = rt.workflow.list_instances(status=status_filter)
    return [
        {
            "instance_id": i.instance_id,
            "workflow_id": i.workflow_id,
            "status": i.status.value,
            "created_at": i.created_at.isoformat(),
            "current_step": i.current_step_index,
            "total_steps": len(i.steps),
        }
        for i in instances
    ]


@router.get("/instances/{instance_id}")
async def get_instance(instance_id: str):
    """Get a specific workflow instance."""
    rt = _get_runtime()
    if rt.workflow:
        instance = rt.workflow.get_instance(instance_id)
        if instance:
            return instance
    raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")


@router.post("/instances/{instance_id}/advance")
async def advance_instance(instance_id: str, step_output: Optional[Dict[str, Any]] = None):
    """Advance a workflow to the next step."""
    rt = _get_runtime()
    if not rt.workflow:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    try:
        running = await rt.workflow.advance(instance_id, step_output=step_output)
        instance = rt.workflow.get_instance(instance_id)
        return {"instance_id": instance_id, "status": instance.status.value, "running": running}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/instances/{instance_id}/cancel")
async def cancel_instance(instance_id: str):
    """Cancel a workflow instance."""
    rt = _get_runtime()
    if not rt.workflow:
        raise HTTPException(status_code=503, detail="Workflow engine not available")
    try:
        await rt.workflow.cancel(instance_id)
        return {"instance_id": instance_id, "status": "cancelled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Event Routes ────────────────────────────────────────────────────────

@router.get("/events/types")
async def list_event_types():
    """List all registered event types."""
    rt = _get_runtime()
    if rt.event:
        return [{"name": name, "channel": et.channel, "description": et.description}
                for name, et in rt.event.list_event_types().items()]
    return []


@router.post("/events/publish")
async def publish_event(event_type: str, source: str, payload: Optional[Dict[str, Any]] = None,
                        correlation_id: Optional[str] = None):
    """Publish an event to the event bus."""
    rt = _get_runtime()
    if not rt.event:
        raise HTTPException(status_code=503, detail="Event engine not available")
    try:
        await rt.event.publish(
            event_type=event_type,
            source=source,
            payload=payload,
            correlation_id=correlation_id,
        )
        return {"event_type": event_type, "published": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ── Capability Routes ───────────────────────────────────────────────────

@router.get("/capabilities")
async def list_capabilities(search: Optional[str] = None):
    """List capabilities, optionally filtered by search query."""
    rt = _get_runtime()
    if rt.executive:
        caps = rt.executive.search_capabilities(search) if search else \
               rt.executive.list_capabilities()
        return [{"id": c.id, "category": c.category, "name": c.name,
                 "level": c.level, "agents": c.agents}
                for c in caps]
    return []


@router.get("/capabilities/{cap_id}")
async def get_capability(cap_id: str):
    """Get a specific capability."""
    rt = _get_runtime()
    if rt.executive:
        cap = rt.executive.get_capability(cap_id)
        if cap:
            return cap
    raise HTTPException(status_code=404, detail=f"Capability {cap_id} not found")


# ── Memory Routes ───────────────────────────────────────────────────────

@router.get("/memory/{agent_id}")
async def get_agent_memory(agent_id: str, org: str = "", dept: str = ""):
    """Get resolved memory context for an agent."""
    rt = _get_runtime()
    if rt.memory:
        context = rt.memory.get_resolved_context(agent_id, org, dept)
        return {"agent_id": agent_id, "files": list(context.keys()), "content": context}
    return {"error": "Memory not available"}


# ── Approval Routes ─────────────────────────────────────────────────────

@router.get("/approvals")
async def list_approvals(status: Optional[str] = None):
    """List approval requests."""
    rt = _get_runtime()
    if rt.approval:
        status_filter = ApprovalStatus(status) if status else None
        return [{"approval_id": a.approval_id, "workflow_id": a.workflow_instance_id,
                 "step_name": a.step_name, "status": a.status.value,
                 "requested_by": a.requested_by, "requested_at": a.requested_at.isoformat()}
                for a in rt.approval.list_approvals(status=status_filter)]
    return []


@router.post("/approvals/{approval_id}/respond")
async def respond_to_approval(approval_id: str, request: ApprovalResponse):
    """Respond to an approval request (approve or reject)."""
    rt = _get_runtime()
    if not rt.approval:
        raise HTTPException(status_code=503, detail="Approval manager not available")
    try:
        if request.approved:
            await rt.approval.approve(approval_id, request.approved_by, request.notes)
        else:
            await rt.approval.reject(approval_id, request.approved_by, request.notes)
        return {"approval_id": approval_id, "approved": request.approved}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))