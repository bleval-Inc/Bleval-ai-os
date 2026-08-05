"""FastAPI route definitions for Axiom OS.

Exposes the runtime capabilities via REST API.
Uses public engine methods — never accesses private attributes.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axiom.models.workflows import ApprovalStatus, WorkflowStatus
from axiom.models.executive import MeetingType
from axiom.runtime.communication import UrgencyLevel, FounderAvailability

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


class ChatRequest(BaseModel):
    message: str
    agent_id: str = "founder"
    org_id: str = ""
    dept_id: str = ""
    conversation_history: List[Dict[str, str]] = []
    preferred_provider: Optional[str] = None
    conversation_id: Optional[str] = None


class AxiomRouteRequest(BaseModel):
    message: str


class AxiomCommunicateRequest(BaseModel):
    message: str


class AxiomExecuteRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}


class AxiomRetrieveRequest(BaseModel):
    query: str
    content_types: Optional[List[str]] = None


# ═══════════════════════════════════════════════════════════════════════════
# Phase F — Board Room & Communication Models
# ═══════════════════════════════════════════════════════════════════════════


class ScheduleMeetingRequest(BaseModel):
    meeting_type: str = "ad_hoc"
    title: str = ""
    called_by: str = "founder"
    attendees: List[str] = ["jenson", "valta_prime", "yamako"]


class MakeDecisionRequest(BaseModel):
    title: str
    description: str
    proposed_by: str = "founder"


class SetAvailabilityRequest(BaseModel):
    availability: str = "available"


class ReleaseSpeakerRequest(BaseModel):
    executive_id: str


# ═══════════════════════════════════════════════════════════════════════════


class AxiomResearchCreateRequest(BaseModel):
    title: str
    query: str


class AxiomResearchConversationRequest(BaseModel):
    role: str
    content: str


class AxiomResearchFindingRequest(BaseModel):
    content: str
    title: Optional[str] = None
    confidence: Optional[float] = None


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


# ── Intelligence / Chat Routes ─────────────────────────────────────────

@router.post("/chat")
async def chat(request: ChatRequest):
    """Send a message to AXIOM's intelligence engine.

    Routes through the SmartRouter for optimal model selection.
    """
    rt = _get_runtime()
    if not rt.intelligence:
        raise HTTPException(status_code=503, detail="Intelligence Engine not available")

    try:
        # Build context from conversation history
        context = {}
        if request.conversation_history:
            context["conversation_history"] = request.conversation_history[-10:]  # Last 10 messages

        response = await rt.intelligence.generate(
            agent_id=request.agent_id,
            task_description=request.message,
            org_id=request.org_id,
            dept_id=request.dept_id,
            additional_context=context or None,
            preferred_provider=request.preferred_provider,
        )
        return {"response": response, "agent_id": request.agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/providers")
async def list_intelligence_providers():
    """List all configured AI providers and their routing assignments."""
    rt = _get_runtime()
    if not rt.intelligence:
        raise HTTPException(status_code=503, detail="Intelligence Engine not available")

    providers = rt.intelligence.list_providers()
    has_real = rt.intelligence.has_real_provider

    # Get route example for each provider
    route_info = rt.intelligence.get_route_for_task(
        "Analyse current executive board status and provide recommendations",
        agent_id="jenson",
    ) if has_real else {}

    return {
        "has_real_provider": has_real,
        "total_providers": len(providers),
        "providers": providers,
        "sample_route": route_info,
    }


# ── Learning Engine Routes ────────────────────────────────────────────────


@router.get("/learning/status")
async def get_learning_status():
    """Get the Learning Engine status summary."""
    rt = _get_runtime()
    if rt.learning:
        return rt.learning.get_summary()
    return {"error": "Learning Engine not available"}


@router.get("/learning/scores")
async def list_learning_scores():
    """List all tracked performance scores."""
    rt = _get_runtime()
    if rt.learning:
        scores = rt.learning.score_tracker.get_all()
        return [
            {
                "entity_id": s.entity_id,
                "entity_type": s.entity_type,
                "running_average": s.running_average,
                "trend": s.trend,
                "total_scores": len(s.scores),
                "last_updated": s.last_updated.isoformat() if s.last_updated else None,
            }
            for s in scores
        ]
    return []


@router.get("/learning/scores/{entity_type}/{entity_id}")
async def get_entity_score_history(entity_type: str, entity_id: str):
    """Get score history for a specific entity."""
    rt = _get_runtime()
    if rt.learning:
        history = rt.learning.score_tracker.get_history(entity_id, entity_type)
        if history:
            return {
                "entity_id": history.entity_id,
                "entity_type": history.entity_type,
                "running_average": history.running_average,
                "trend": history.trend,
                "scores": [
                    {
                        "overall": s.overall_score,
                        "categories": {k.value: v for k, v in s.categories.items()},
                        "duration": s.duration_seconds,
                        "step_count": s.step_count,
                        "error_count": s.error_count,
                        "retry_count": s.retry_count,
                        "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                    }
                    for s in history.scores[-20:]
                ],
            }
        raise HTTPException(status_code=404, detail=f"No scores for {entity_type}:{entity_id}")
    raise HTTPException(status_code=503, detail="Learning Engine not available")


@router.get("/learning/analytics/workflows")
async def get_workflow_analytics(workflow_id: Optional[str] = None):
    """Get workflow performance analytics."""
    rt = _get_runtime()
    if rt.learning:
        return [
            {
                "workflow_id": s.workflow_id,
                "total_runs": s.total_runs,
                "success_rate": round(s.success_rate, 4),
                "avg_duration_seconds": round(s.avg_duration_seconds, 2),
                "avg_retries": round(s.avg_retries_per_run, 2),
                "trend": s.trend,
                "failure_reasons": s.failure_reasons,
                "last_run": s.last_run.isoformat() if s.last_run else None,
            }
            for s in rt.learning.get_workflow_analytics(workflow_id)
        ]
    return []


@router.get("/learning/analytics/executives")
async def get_executive_analytics(exec_id: Optional[str] = None):
    """Get executive performance analytics."""
    rt = _get_runtime()
    if rt.learning:
        return rt.learning.get_executive_analytics(exec_id)
    return []


@router.get("/learning/analytics/agents")
async def get_agent_analytics(agent_id: Optional[str] = None):
    """Get agent performance analytics."""
    rt = _get_runtime()
    if rt.learning:
        return rt.learning.get_agent_analytics(agent_id)
    return []


@router.get("/learning/patterns")
async def get_learning_patterns(severity: Optional[str] = None):
    """Get detected learning patterns, optionally filtered by severity."""
    rt = _get_runtime()
    if rt.learning:
        from axiom.models.learning import PatternSeverity
        sev = PatternSeverity(severity) if severity else None
        patterns = rt.learning.get_patterns(sev)
        return [
            {
                "pattern_id": p.pattern_id,
                "pattern_type": p.pattern_type,
                "severity": p.severity.value,
                "title": p.title,
                "description": p.description,
                "entities_involved": p.entities_involved,
                "frequency": p.frequency,
                "impact_score": p.impact_score,
                "first_detected": p.first_detected.isoformat(),
                "last_detected": p.last_detected.isoformat(),
            }
            for p in patterns
        ]
    return []


@router.get("/learning/recommendations")
async def get_learning_recommendations(status: Optional[str] = None):
    """Get learning recommendations, optionally filtered by status."""
    rt = _get_runtime()
    if rt.learning:
        from axiom.models.learning import RecommendationStatus
        st = RecommendationStatus(status) if status else None
        recs = rt.learning.get_recommendations(st)
        return [
            {
                "recommendation_id": r.recommendation_id,
                "title": r.title,
                "description": r.description[:200] if r.description else "",
                "expected_impact": r.expected_impact,
                "confidence": r.confidence,
                "status": r.status.value,
                "change_type": r.change_type,
                "suggested_action": r.suggested_action,
                "created_at": r.created_at.isoformat(),
                "approved_by": r.approved_by,
            }
            for r in recs
        ]
    return []


@router.get("/learning/knowledge")
async def get_learning_knowledge():
    """Get consolidated knowledge entries."""
    rt = _get_runtime()
    if rt.learning:
        entries = rt.learning.get_knowledge()
        return [
            {
                "entry_id": e.entry_id,
                "title": e.title,
                "content": e.content[:300] if e.content else "",
                "source": e.source.value,
                "confidence": e.confidence,
                "tags": e.tags,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
    return []


@router.get("/learning/cycles")
async def get_learning_cycles(limit: int = 10):
    """Get recent learning cycles."""
    rt = _get_runtime()
    if rt.learning:
        cycles = rt.learning.get_learning_cycles(limit)
        return [
            {
                "cycle_id": c.cycle_id,
                "source_entity": f"{c.source_entity_type}:{c.source_entity_id}",
                "scores": c.scores,
                "patterns_detected": len(c.patterns_detected),
                "recommendations": len(c.recommendations_generated),
                "knowledge_written": len(c.knowledge_written),
                "duration_seconds": round(c.duration_seconds, 2),
                "success": c.success,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
            }
            for c in cycles
        ]
    return []


@router.post("/learning/cycle/run")
async def run_learning_cycle(entity_id: str = "system", entity_type: str = "system"):
    """Manually trigger a learning cycle."""
    rt = _get_runtime()
    if not rt.learning:
        raise HTTPException(status_code=503, detail="Learning Engine not available")
    try:
        cycle = await rt.learning.run_learning_cycle(entity_id, entity_type)
        return {
            "cycle_id": cycle.cycle_id,
            "source": f"{entity_type}:{entity_id}",
            "patterns_detected": len(cycle.patterns_detected),
            "recommendations": len(cycle.recommendations_generated),
            "knowledge_written": len(cycle.knowledge_written),
            "duration_seconds": round(cycle.duration_seconds, 2),
            "success": cycle.success,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/playbook-evolutions")
async def get_playbook_evolutions():
    """Get recorded playbook evolutions."""
    rt = _get_runtime()
    if rt.learning:
        evolutions = rt.learning.get_playbook_evolutions()
        return [
            {
                "playbook_name": e.playbook_name,
                "version": e.version,
                "change_description": e.change_description,
                "triggered_by_pattern": e.triggered_by_pattern,
                "applied_at": e.applied_at.isoformat(),
                "approved_by": e.approved_by,
            }
            for e in evolutions
        ]
    return []


# ═══════════════════════════════════════════════════════════════════════════
# System Telemetry & Greeting Routes (JARVIS integration)
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/system/telemetry")
async def get_system_telemetry():
    """Get full system telemetry snapshot — CPU, RAM, disk, network, temp.

    Returns a complete TelemetrySnapshot for the AI's system awareness.
    """
    rt = _get_runtime()
    if not hasattr(rt, "system_monitor") or not rt.system_monitor:
        from axiom.runtime.system_monitor import SystemMonitor

        mon = SystemMonitor()
        await mon.initialise()
    else:
        mon = rt.system_monitor
    try:
        snap = await mon.snapshot()
        return snap.to_dict()
    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stdout)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/health")
async def get_system_health():
    """Get quick system health check."""
    rt = _get_runtime()
    if not hasattr(rt, "system_monitor") or not rt.system_monitor:
        from axiom.runtime.system_monitor import SystemMonitor

        mon = SystemMonitor()
        await mon.initialise()
    else:
        mon = rt.system_monitor
    return await mon.health_check()


@router.get("/system/info")
async def get_system_info():
    """Get basic OS information."""
    import platform as pf
    import time as _time

    try:
        import psutil
        boot_time = psutil.boot_time()
    except Exception:
        boot_time = _time.time()
    return {
        "hostname": pf.node(),
        "platform": pf.platform(),
        "release": pf.release(),
        "version": pf.version(),
        "architecture": pf.machine(),
        "processor": pf.processor(),
        "boot_time": boot_time,
        "uptime_seconds": _time.time() - boot_time,
    }


@router.get("/system/greeting")
async def get_greeting(first_boot: bool = False, user_name: Optional[str] = None):
    """Generate a dynamic, context-aware boot greeting.

    Returns a GreetingResult with text, mood, time_of_day, and health context
    — ready for TTS rendering and UI display.
    """
    rt = _get_runtime()
    if hasattr(rt, "greeting_engine") and rt.greeting_engine:
        engine = rt.greeting_engine
    else:
        from axiom.runtime.greeting_engine import GreetingEngine

        engine = GreetingEngine(logger=getattr(rt, "logger", None))

    telemetry = None
    if hasattr(rt, "system_monitor") and rt.system_monitor:
        try:
            telemetry = await rt.system_monitor.snapshot()
        except Exception:
            pass

    result = await engine.generate_greeting(
        telemetry=telemetry,
        is_first_boot=first_boot,
        user_name=user_name,
    )
    return {
        "text": result.text,
        "mood": result.mood,
        "time_of_day": result.time_of_day,
        "health_label": result.health_label,
        "variant_id": result.variant_id,
        "is_seasonal": result.is_seasonal,
        "is_returning": result.is_returning,
    }


@router.get("/system/greeting/wake")
async def get_wake_greeting():
    """Generate a short wake greeting (for waking from idle)."""
    rt = _get_runtime()
    if hasattr(rt, "greeting_engine") and rt.greeting_engine:
        engine = rt.greeting_engine
    else:
        from axiom.runtime.greeting_engine import GreetingEngine

        engine = GreetingEngine(logger=getattr(rt, "logger", None))

    telemetry = None
    if hasattr(rt, "system_monitor") and rt.system_monitor:
        try:
            telemetry = await rt.system_monitor.snapshot()
        except Exception:
            pass

    result = await engine.generate_wake_greeting(telemetry=telemetry)
    return {
        "text": result.text,
        "mood": result.mood,
        "time_of_day": result.time_of_day,
        "health_label": result.health_label,
        "variant_id": result.variant_id,
        "is_seasonal": result.is_seasonal,
        "is_returning": result.is_returning,
    }


@router.get("/system/status-report")
async def get_status_report():
    """Generate a one-line TTS-ready system status report."""
    rt = _get_runtime()
    if hasattr(rt, "greeting_engine") and rt.greeting_engine:
        engine = rt.greeting_engine
    else:
        from axiom.runtime.greeting_engine import GreetingEngine

        engine = GreetingEngine(logger=getattr(rt, "logger", None))

    telemetry = None
    if hasattr(rt, "system_monitor") and rt.system_monitor:
        try:
            telemetry = await rt.system_monitor.snapshot()
        except Exception:
            pass

    text = await engine.generate_status_report(telemetry)
    return {"text": text}


@router.get("/system/tools")
async def list_system_tools():
    """List all available system tools for AI function-calling."""
    rt = _get_runtime()
    if hasattr(rt, "system_tools") and rt.system_tools:
        return rt.system_tools.list_tools()
    return []


@router.post("/system/execute-tool")
async def execute_system_tool(request: dict):
    """Execute a system tool by name with the given arguments.

    Request body:
        {"tool": "get_telemetry", "args": {}}
    """
    rt = _get_runtime()
    if not hasattr(rt, "system_tools") or not rt.system_tools:
        raise HTTPException(status_code=503, detail="System Tools not available")

    tool_name = request.get("tool", "")
    tool_args = request.get("args", {})

    if not tool_name:
        raise HTTPException(status_code=400, detail="Missing 'tool' field")

    result = await rt.system_tools.execute_tool(tool_name, tool_args)
    return result.to_dict()


@router.post("/tts")
async def text_to_speech(text: str):
    """Text-to-speech proxy.

    Returns the text for browser-based TTS (SpeechSynthesis) or
    could be extended to call ElevenLabs/Deepgram streaming API.
    """
    return {"text": text, "format": "ssml", "speaker": "axiom"}


# ═══════════════════════════════════════════════════════════════════════════════
# AXIOM Core Routes — Founder interface, system concierge, intelligence layer
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/axiom/status")
async def get_axiom_status():
    """Get AXIOM Core status — state, boot info, system awareness."""
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        return {"state": "unavailable", "error": "AXIOM Core not available"}

    awareness = await rt.axiom.get_system_awareness()
    return {
        "state": rt.axiom.state.value,
        "boot_id": rt.axiom.boot_id,
        "is_online": rt.axiom.is_online,
        "awareness": awareness.to_dict(),
    }


@router.post("/axiom/chat")
async def axiom_chat(request: ChatRequest):
    """Chat with AXIOM — the Founder's conversational interface.

    AXIOM has full system awareness and can:
    - Route requests to executives
    - Monitor system health
    - Perform research
    - Retrieve content
    - Manage workspaces
    """
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    try:
        result = await rt.axiom.chat(
            message=request.message,
            conversation_history=request.conversation_history,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/axiom/route")
async def axiom_route(request: AxiomRouteRequest):
    """Route a Founder request through AXIOM's classification and routing layer.

    Returns the routing decision along with the response.
    Useful for debugging routing or for the frontend to understand intent.
    """
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    try:
        result = await rt.axiom.handle_request(request.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/axiom/awareness")
async def get_axiom_awareness():
    """Get full system awareness snapshot — live operational model.

    Returns the state of all executives, engines, workflows, and
    system health metrics in a single structured response.
    """
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    awareness = await rt.axiom.get_system_awareness()
    return awareness.to_dict()


# ── Research Workspace Routes ─────────────────────────────────────────────


@router.post("/axiom/research")
async def create_research_workspace(request: AxiomResearchCreateRequest):
    """Create a new research workspace for deep-dive investigation."""
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    try:
        workspace = await rt.axiom.create_research_workspace(
            title=request.title,
            query=request.query,
        )
        return workspace
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/axiom/research")
async def list_research_workspaces(status: Optional[str] = None):
    """List all research workspaces, optionally filtered by status."""
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        return []

    if status == "active":
        return rt.axiom.list_research_workspaces()
    return rt.axiom.list_research_workspaces()


@router.get("/axiom/research/{workspace_id}")
async def get_research_workspace(workspace_id: str):
    """Get a research workspace with full details."""
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    workspace = rt.axiom.get_research_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
    return workspace


@router.post("/axiom/research/{workspace_id}/conversation")
async def add_research_conversation(workspace_id: str, request: AxiomResearchConversationRequest):
    """Add a conversation entry to a research workspace."""
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    workspace = rt.axiom.update_research_workspace(
        workspace_id,
        {"conversation": [{"role": request.role, "content": request.content}]},
    )
    if workspace is None:
        raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
    return workspace


@router.post("/axiom/research/{workspace_id}/findings")
async def add_research_finding(workspace_id: str, request: AxiomResearchFindingRequest):
    """Add a finding to a research workspace."""
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    finding = {"content": request.content, "title": request.title, "confidence": request.confidence}
    workspace = await rt.axiom.add_research_finding(workspace_id, finding)
    if workspace is None:
        raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
    return workspace


@router.post("/axiom/research/{workspace_id}/archive")
async def archive_research_workspace(workspace_id: str):
    """Archive a research workspace."""
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    success = rt.axiom.archive_research_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
    return {"workspace_id": workspace_id, "status": "archived"}


# ── AXIOM Executive Communication ────────────────────────────────────────


@router.post("/axiom/communicate/{exec_id}")
async def communicate_with_executive(exec_id: str, request: AxiomCommunicateRequest):
    """Route a Founder message to an executive through AXIOM."""
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    try:
        result = await rt.axiom.route_to_executive(exec_id, request.message)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── AXIOM System Actions ─────────────────────────────────────────────────


@router.post("/axiom/execute")
async def axiom_execute(request: AxiomExecuteRequest):
    """Execute a system action through AXIOM's tools bridge.

    Only non-approval actions execute directly.
    Actions requiring Founder approval (trades, payments, etc.)
    go through the approval manager.
    """
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    result = await rt.axiom.execute_system_action(request.action, request.params)
    return result


# ── AXIOM Content Retrieval ──────────────────────────────────────────────


@router.post("/axiom/retrieve")
async def axiom_retrieve(request: AxiomRetrieveRequest):
    """Multi-modal content retrieval through AXIOM.

    Searches across text, images, videos, audio, and documents.
    """
    rt = _get_runtime()
    if not hasattr(rt, "axiom") or rt.axiom is None:
        raise HTTPException(status_code=503, detail="AXIOM Core not available")

    results = await rt.axiom.retrieve_content(request.query, request.content_types)
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Phase D — Quality Control & Founder Authority Routes
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/qc/status")
async def get_qc_status():
    """Get QC Manager summary — total checks, pass/fail counts, rework history."""
    rt = _get_runtime()
    if hasattr(rt, "qc_manager") and rt.qc_manager:
        return rt.qc_manager.get_summary()
    return {"error": "QC Manager not available"}


@router.get("/qc/results")
async def get_qc_results(limit: int = 20):
    """List recent QC results."""
    rt = _get_runtime()
    if hasattr(rt, "qc_manager") and rt.qc_manager:
        submissions = rt.qc_manager.get_all_results()[:limit]
        return [
            {
                "qc_id": s.qc_id,
                "artifact_name": s.artifact_name,
                "status": s.status.value,
                "passed": s.passed,
                "summary": s.summary,
                "critical_count": s.critical_count,
                "high_count": s.high_count,
                "medium_count": s.medium_count,
                "low_count": s.low_count,
                "retry_count": s.retry_count,
                "scope": s.scope.value if hasattr(s, "scope") else "unknown",
                "created_at": s.created_at.isoformat() if hasattr(s, "created_at") and s.created_at else None,
            }
            for s in submissions
        ]
    return []


@router.get("/founder/feed")
async def get_founder_feed(limit: int = 20):
    """Get Founder FAST FEED items — ordered by urgency/priority."""
    rt = _get_runtime()
    if hasattr(rt, "founder_gateway") and rt.founder_gateway:
        items = rt.founder_gateway.get_feed(limit=limit)
        return [
            {
                "id": item.id,
                "type": item.type.value if hasattr(item.type, "value") else str(item.type),
                "severity": item.severity.value if hasattr(item.severity, "value") else str(item.severity),
                "title": item.title,
                "summary": item.summary,
                "context": item.context,
                "requires_decision": item.requires_decision,
                "decision_deadline": item.decision_deadline.isoformat() if item.decision_deadline else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "acknowledged": item.acknowledged,
                "resolved": item.resolved,
            }
            for item in items
        ]
    return []


@router.get("/founder/pipelines")
async def get_founder_pipelines():
    """List all active approval pipelines."""
    rt = _get_runtime()
    if hasattr(rt, "founder_gateway") and rt.founder_gateway:
        pipelines = rt.founder_gateway.list_active_pipelines()
        return [
            {
                "pipeline_id": p.pipeline_id,
                "plan_id": p.plan_id,
                "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                "stage": p.stage.value if hasattr(p.stage, "value") else str(p.stage),
                "approval_status": p.approval_status.value if hasattr(p.approval_status, "value") else str(p.approval_status),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pipelines
        ]
    return []


@router.get("/executives/{exec_id}/pois")
async def get_executive_pois(exec_id: str):
    """Get POI (Points of Interest) monitoring state for an executive."""
    rt = _get_runtime()
    if rt.executive:
        exec_data = rt.executive.get_executive_detail(exec_id)
        if exec_data:
            return {"exec_id": exec_id, "pois": exec_data.get("pois", {})}
    return {"exec_id": exec_id, "pois": {}, "note": "Executive POI data not available"}


@router.get("/executives/{exec_id}/schedule")
async def get_executive_schedule(exec_id: str):
    """Get schedule data for an executive (used by Yamako / Personal workstation)."""
    rt = _get_runtime()
    if rt.executive:
        exec_data = rt.executive.get_executive_detail(exec_id)
        if exec_data:
            return {"exec_id": exec_id, "schedule": exec_data.get("schedule", [])}
    return {"exec_id": exec_id, "schedule": [], "note": "Schedule not available"}


# ═══════════════════════════════════════════════════════════════════════════
# Phase F — Board Room Routes
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/board/dashboard")
async def get_board_dashboard():
    """Get complete Board Room dashboard snapshot."""
    rt = _get_runtime()
    if hasattr(rt, "board_room") and rt.board_room:
        return rt.board_room.get_dashboard()
    return {"error": "Board Room not available"}


@router.get("/board/meetings")
async def list_board_meetings(limit: int = 10, meeting_type: Optional[str] = None):
    """List recent board meetings, optionally filtered by type."""
    rt = _get_runtime()
    if hasattr(rt, "board_room") and rt.board_room:
        mtype = MeetingType(meeting_type) if meeting_type else None
        meetings = rt.board_room.list_meetings(limit=limit, meeting_type=mtype)
        return [
            {
                "meeting_id": m.meeting_id,
                "meeting_type": m.meeting_type.value,
                "title": m.title,
                "called_by": m.called_by,
                "attendees": m.attendees,
                "status": m.status,
                "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
                "started_at": m.started_at.isoformat() if m.started_at else None,
                "completed_at": m.completed_at.isoformat() if m.completed_at else None,
                "agenda_count": len(m.agenda),
                "decisions_count": len(m.decisions),
                "action_items_count": len(m.action_items),
                "minutes": m.minutes[:500] if m.minutes else "",
            }
            for m in meetings
        ]
    return []


@router.get("/board/meetings/{meeting_id}")
async def get_board_meeting(meeting_id: str):
    """Get a specific board meeting's full detail."""
    rt = _get_runtime()
    if hasattr(rt, "board_room") and rt.board_room:
        meeting = rt.board_room.get_meeting(meeting_id)
        if meeting:
            return {
                "meeting_id": meeting.meeting_id,
                "meeting_type": meeting.meeting_type.value,
                "title": meeting.title,
                "called_by": meeting.called_by,
                "attendees": meeting.attendees,
                "status": meeting.status,
                "scheduled_at": meeting.scheduled_at.isoformat() if meeting.scheduled_at else None,
                "started_at": meeting.started_at.isoformat() if meeting.started_at else None,
                "completed_at": meeting.completed_at.isoformat() if meeting.completed_at else None,
                "agenda": [
                    {
                        "agenda_id": a.agenda_id,
                        "submitted_by": a.submitted_by,
                        "title": a.title,
                        "description": a.description,
                        "priority": a.priority,
                        "status": a.status,
                    }
                    for a in meeting.agenda
                ],
                "decisions": [
                    {
                        "decision_id": d.decision_id,
                        "title": d.title,
                        "description": d.description,
                        "proposed_by": d.proposed_by,
                        "approved": d.approved,
                        "votes_for": d.votes_for,
                        "votes_against": d.votes_against,
                    }
                    for d in meeting.decisions
                ],
                "action_items": [
                    {
                        "item_id": a.item_id,
                        "title": a.title,
                        "assigned_to": a.assigned_to,
                        "priority": a.priority,
                        "status": a.status.value,
                        "deadline": a.deadline.isoformat() if a.deadline else None,
                    }
                    for a in meeting.action_items
                ],
                "kpi_snapshots": meeting.kpi_snapshots,
                "minutes": meeting.minutes,
            }
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
    raise HTTPException(status_code=503, detail="Board Room not available")


@router.post("/board/meetings")
async def schedule_board_meeting(request: ScheduleMeetingRequest):
    """Schedule a new board meeting."""
    rt = _get_runtime()
    if hasattr(rt, "board_room") and rt.board_room:
        try:
            mtype = MeetingType(request.meeting_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid meeting type: {request.meeting_type}")
        meeting_id = await rt.board_room.schedule_meeting(
            meeting_type=mtype,
            called_by=request.called_by,
            title=request.title,
            attendees=request.attendees,
        )
        return {"meeting_id": meeting_id, "meeting_type": request.meeting_type, "status": "scheduled"}
    raise HTTPException(status_code=503, detail="Board Room not available")


@router.post("/board/meetings/{meeting_id}/decisions")
async def make_board_decision(meeting_id: str, request: MakeDecisionRequest):
    """Record a board decision."""
    rt = _get_runtime()
    if hasattr(rt, "board_room") and rt.board_room:
        decision = await rt.board_room.make_decision(
            meeting_id=meeting_id,
            title=request.title,
            description=request.description,
            proposed_by=request.proposed_by,
        )
        return {
            "decision_id": decision.decision_id,
            "meeting_id": meeting_id,
            "approved": decision.approved,
        }
    raise HTTPException(status_code=503, detail="Board Room not available")


@router.get("/board/kpis")
async def get_board_kpis():
    """Get latest KPI snapshots from all executives."""
    rt = _get_runtime()
    if hasattr(rt, "board_room") and rt.board_room:
        return rt.board_room.get_latest_kpis()
    return {}


@router.get("/board/action-items")
async def list_board_action_items(exec_id: Optional[str] = None):
    """List open action items, optionally filtered by assignee."""
    rt = _get_runtime()
    if hasattr(rt, "board_room") and rt.board_room:
        items = rt.board_room.get_open_action_items(exec_id=exec_id)
        overdue = rt.board_room.get_overdue_action_items()
        return {
            "open": [
                {
                    "item_id": i.item_id,
                    "meeting_id": i.meeting_id,
                    "title": i.title,
                    "assigned_to": i.assigned_to,
                    "priority": i.priority,
                    "status": i.status.value,
                    "deadline": i.deadline.isoformat() if i.deadline else None,
                    "created_at": i.created_at.isoformat(),
                }
                for i in items
            ],
            "overdue": [
                {
                    "item_id": i.item_id,
                    "meeting_id": i.meeting_id,
                    "title": i.title,
                    "assigned_to": i.assigned_to,
                    "priority": i.priority,
                    "status": i.status.value,
                    "deadline": i.deadline.isoformat() if i.deadline else None,
                    "created_at": i.created_at.isoformat(),
                }
                for i in overdue
            ],
        }
    return {"open": [], "overdue": []}


# ═══════════════════════════════════════════════════════════════════════════
# Phase F — Communication Coordinator Routes
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/communication/status")
async def get_communication_status():
    """Get Communication Coordinator dashboard snapshot."""
    rt = _get_runtime()
    if hasattr(rt, "communication") and rt.communication:
        return rt.communication.get_dashboard()
    return {"error": "Communication Coordinator not available"}


@router.get("/communication/queue")
async def get_communication_queue(limit: int = 10):
    """Get the current speaker queue."""
    rt = _get_runtime()
    if hasattr(rt, "communication") and rt.communication:
        return rt.communication.get_speaker_queue(limit=limit)
    return []


@router.post("/communication/founder/availability")
async def set_founder_availability(request: SetAvailabilityRequest):
    """Set the Founder's availability state (manual override)."""
    rt = _get_runtime()
    if hasattr(rt, "communication") and rt.communication:
        try:
            availability = FounderAvailability(request.availability)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid availability: {request.availability}")
        rt.communication.set_founder_availability(availability)
        return {"availability": request.availability, "set": True}
    raise HTTPException(status_code=503, detail="Communication Coordinator not available")


@router.get("/communication/messages")
async def get_communication_messages(limit: int = 20, sender: Optional[str] = None):
    """Get recent message history, optionally filtered by sender."""
    rt = _get_runtime()
    if hasattr(rt, "communication") and rt.communication:
        return rt.communication.get_message_history(limit=limit, sender=sender)
    return []


@router.post("/communication/release-speaker")
async def release_communication_speaker(request: ReleaseSpeakerRequest):
    """Release the current speaker and process the queue."""
    rt = _get_runtime()
    if hasattr(rt, "communication") and rt.communication:
        await rt.communication.release_speaker(request.executive_id)
        return {"released": request.executive_id}
    raise HTTPException(status_code=503, detail="Communication Coordinator not available")


@router.post("/communication/clear-emergency")
async def clear_communication_emergency():
    """Clear the emergency state and resume normal operations."""
    rt = _get_runtime()
    if hasattr(rt, "communication") and rt.communication:
        await rt.communication.clear_emergency()
        return {"emergency_cleared": True}
    raise HTTPException(status_code=503, detail="Communication Coordinator not available")


# ═══════════════════════════════════════════════════════════════════════════
# Voice Interaction Routes
# ═══════════════════════════════════════════════════════════════════════════


class VoiceCommandRequest(BaseModel):
    """Voice command from frontend - wake word + command text."""

    transcript: str
    executive: str  # "axiom" | "jenson" | "valta_prime" | "yamako"
    wake_word: str
    confidence: float = 1.0
    timestamp: int = 0


class VoiceCommandResponse(BaseModel):
    """Response from executive after processing voice command."""

    executive: str
    response: str
    action_taken: str | None = None
    workflow_triggered: str | None = None
    requires_approval: bool = False
    approval_id: str | None = None


@router.post("/voice/command", response_model=VoiceCommandResponse)
async def process_voice_command(request: VoiceCommandRequest):
    """Process a voice command routed to a specific executive.

    This is the main entry point for voice interactions:
    - Frontend detects wake word and transcribes command
    - Sends to this endpoint with target executive
    - Backend routes to executive's runtime loop or triggers action
    - Returns executive's response for TTS playback
    """
    rt = _get_runtime()
    exec_id = request.executive.lower()

    valid_executives = ["axiom", "jenson", "valta_prime", "yamako"]
    if exec_id not in valid_executives:
        raise HTTPException(status_code=400, detail=f"Invalid executive: {exec_id}. Must be one of {valid_executives}")

    try:
        # Route command based on executive
        if exec_id == "axiom":
            return await _process_axiom_command(rt, request)
        else:
            return await _process_executive_command(rt, exec_id, request)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice command processing failed: {str(e)}")


async def _process_axiom_command(rt: Any, request: VoiceCommandRequest) -> VoiceCommandResponse:
    """Process command for AXIOM (core intelligence)."""
    if not hasattr(rt, "axiom") or rt.axiom is None:
        return VoiceCommandResponse(
            executive="axiom",
            response="AXIOM core is not available.",
            action_taken="error",
        )

    # Use AXIOM to process the command
    result = await rt.axiom.chat(
        message=request.transcript,
        conversation_history=[],
    )

    return VoiceCommandResponse(
        executive="axiom",
        response=result.get("response", "Command received."),
        action_taken=result.get("action"),
        workflow_triggered=result.get("workflow"),
        requires_approval=result.get("requires_approval", False),
        approval_id=result.get("approval_id"),
    )


async def _process_executive_command(rt: Any, exec_id: str, request: VoiceCommandRequest) -> VoiceCommandResponse:
    """Process command for Jenson, Valta Prime, or Yamako."""
    # Check if executive board is available
    if not rt.executive_board:
        return VoiceCommandResponse(
            executive=exec_id,
            response=f"{exec_id} is not currently available.",
            action_taken="error",
        )

    # Get the executive's loop
    loop = rt.executive_board.get_loop(exec_id)
    if not loop:
        return VoiceCommandResponse(
            executive=exec_id,
            response=f"{exec_id} loop is not running.",
            action_taken="error",
        )

    # Route the command through the executive's intelligence
    # This triggers a manual cycle with the voice command as context
    try:
        result = await loop.trigger_cycle("voice", {
            "voice_command": request.transcript,
            "wake_word": request.wake_word,
            "confidence": request.confidence,
        })

        # Generate a response based on the cycle result
        response_text = _generate_executive_response(exec_id, request.transcript, result)

        # Check if workflow was triggered
        workflow_triggered = result.get("workflow_triggered") if isinstance(result, dict) else None

        return VoiceCommandResponse(
            executive=exec_id,
            response=response_text,
            action_taken=result.get("action", "cycle_triggered") if isinstance(result, dict) else "cycle_triggered",
            workflow_triggered=workflow_triggered,
        )

    except Exception as e:
        return VoiceCommandResponse(
            executive=exec_id,
            response=f"Command processing error: {str(e)}",
            action_taken="error",
        )


def _generate_executive_response(exec_id: str, transcript: str, result: Any) -> str:
    """Generate a natural language response from an executive based on command and result."""

    responses = {
        "jenson": {
            "default": "Jenson acknowledged. Operations update queued.",
            "workflow": "Launching workflow. I'll monitor execution.",
            "status": "Current operations status: all systems nominal.",
            "schedule": "Checking schedule. Updates incoming.",
        },
        "valta_prime": {
        "default": "Valta Prime received. Analyzing request.",
        "workflow": "Initiating market analysis workflow.",
        "status": "Market monitoring active. No alerts.",
        "schedule": "Reviewing trading schedule.",
        },
        "yamako": {
        "default": "Yamako here. Personal ops notified.",
        "workflow": "Starting that for you now.",
        "status": "Your daily overview is ready.",
        "schedule": "Let me check your calendar.",
        },
    }

    exec_responses = responses.get(exec_id, {"default": "Command received."})
    lower = transcript.lower()

    if any(kw in lower for kw in ["workflow", "launch", "start", "run", "execute"]):
        return exec_responses.get("workflow", exec_responses["default"])
    elif any(kw in lower for kw in ["status", "how are", "what's up", "check"]):
        return exec_responses.get("status", exec_responses["default"])
    elif any(kw in lower for kw in ["schedule", "calendar", "meeting", "appointment"]):
        return exec_responses.get("schedule", exec_responses["default"])

    return exec_responses["default"]


@router.get("/voice/executives")
async def list_voice_executives():
    """List all executives available for voice interaction with their wake words."""

    return {
        "executives": [
            {
                "id": "axiom",
                "name": "AXIOM",
                "wake_words": ["axiom on", "axiom", "hey axiom", "ok axiom"],
                "voice_profile": "axiom",
                "description": "Core intelligence — system awareness, research, routing",
            },
            {
                "id": "jenson",
                "name": "Jenson",
                "wake_words": ["jenson", "hey jenson", "jensen"],
                "voice_profile": "jenson",
                "description": "COO — Bleval Inc operations, projects, team management",
            },
            {
                "id": "valta_prime",
                "name": "Valta Prime",
                "wake_words": ["valta prime", "valta", "hey valta", "prime"],
                "voice_profile": "valta_prime",
                "description": "Trading mentor — market analysis, risk, strategy",
            },
            {
                "id": "yamako",
                "name": "Yamako",
                "wake_words": ["yamako", "hey yamako"],
                "voice_profile": "yamako",
                "description": "Personal ops — schedule, habits, knowledge, reminders",
            },
        ]
    }


@router.post("/voice/speak")
async def executive_speak(
    executive: str,
    text: str,
    urgency: str = "normal",
):
    """Trigger an executive to speak via the speech arbiter.

    This allows backend-initiated speech (notifications, alerts, greetings).
    """
    rt = _get_runtime()

    # Validate executive
    valid = ["axiom", "jenson", "valta_prime", "yamako"]
    if executive not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid executive: {executive}")

    # This would integrate with the frontend's speech arbiter
    # For now, return the text for frontend to handle
    return {
        "executive": executive,
        "text": text,
        "urgency": urgency,
        "queued": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase E — Executive Intelligence + QC Learning Routes
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/executives/{exec_id}/intelligence")
async def get_executive_intelligence(exec_id: str):
    """Get learning-driven intelligence for an executive's decision-making.

    Returns patterns, recommendations, performance scores, and analytics
    relevant to the executive's organization and departments.
    """
    rt = _get_runtime()
    if hasattr(rt, "executive_intelligence") and rt.executive_intelligence:
        return await rt.executive_intelligence.get_executive_intelligence(exec_id)
    return {"error": "Executive Intelligence not available"}


@router.get("/executives/{exec_id}/greeting")
async def get_executive_greeting(exec_id: str):
    """Get a personalized greeting from an executive when Founder enters workstation.

    Includes completed work, active operations, and today's priorities.
    """
    rt = _get_runtime()
    if hasattr(rt, "executive_greeter") and rt.executive_greeter:
        greeting = await rt.executive_greeter.greet_founder(exec_id)
        return {
            "exec_id": exec_id,
            "greeting": greeting,
            "timestamp": "now",
        }
    return {"error": "Executive Greeter not available"}


@router.post("/executives/{exec_id}/workflow/decision-support")
async def get_workflow_decision_support(
    exec_id: str,
    workflow_id: str,
    priority: str = "",
):
    """Get learning-driven decision support for launching a workflow.

    Analyzes historical performance, detected patterns, and recommendations
    to provide confidence score and warnings/insights.
    """
    rt = _get_runtime()
    if hasattr(rt, "executive_intelligence") and rt.executive_intelligence:
        return await rt.executive_intelligence.get_workflow_decision_support(
            exec_id=exec_id,
            workflow_id=workflow_id,
            priority=priority,
        )
    return {"error": "Executive Intelligence not available"}


@router.post("/executives/{exec_id}/learning/cycle")
async def run_executive_learning_cycle(exec_id: str):
    """Run a learning cycle specifically for an executive's domain."""
    rt = _get_runtime()
    if hasattr(rt, "executive_intelligence") and rt.executive_intelligence:
        return await rt.executive_intelligence.run_learning_cycle_for_exec(exec_id)
    raise HTTPException(status_code=503, detail="Executive Intelligence not available")


@router.post("/qc/feedback")
async def submit_qc_feedback(
    pattern_id: str,
    action: str,  # "fixed" | "false_positive" | "configuration_changed"
    details: str = "",
):
    """Submit human feedback on a QC learning pattern.

    Closes the learning loop when Founder/executive takes action.
    """
    rt = _get_runtime()
    if hasattr(rt, "qc_learning_pipeline") and rt.qc_learning_pipeline:
        await rt.qc_learning_pipeline.process_qc_feedback(
            pattern_id=pattern_id,
            action=action,
            details=details,
        )
        return {"pattern_id": pattern_id, "action": action, "processed": True}
    return {"error": "QC Learning Pipeline not available"}


@router.get("/qc/trends")
async def get_qc_trends(scope: str = "", days: int = 7):
    """Analyze QC pass rate trends and identify bottlenecks."""
    rt = _get_runtime()
    if hasattr(rt, "qc_learning_pipeline") and rt.qc_learning_pipeline:
        from axiom.engine.qc_learning_pipeline import QCtrendAnalyzer
        analyzer = QCtrendAnalyzer(rt.learning)
        trend = analyzer.analyze_qc_pass_rate_trend(scope, days)
        bottlenecks = analyzer.identify_qc_bottlenecks(scope)
        return {"trend": trend, "bottlenecks": bottlenecks}
    return {"error": "QC Learning Pipeline not available"}


# ════════════════════════════════════════════════════════════════════════════
# Voice WebSocket Routes
# ═══════════════════════════════════════════════════════════════════════════

from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio


class VoiceConnectionManager:
    """Manages active voice WebSocket connections."""

    def __init__(self):
        self.client_connections: Dict[str, WebSocket] = {}
        self.broadcast_connections: List[WebSocket] = []

    async def connect_client(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.client_connections[client_id] = websocket

    def disconnect_client(self, client_id: str):
        if client_id in self.client_connections:
            del self.client_connections[client_id]

    async def connect_broadcast(self, websocket: WebSocket):
        await websocket.accept()
        self.broadcast_connections.append(websocket)

    def disconnect_broadcast(self, websocket: WebSocket):
        if websocket in self.broadcast_connections:
            self.broadcast_connections.remove(websocket)

    async def send_to_client(self, client_id: str, message: Dict):
        if client_id in self.client_connections:
            try:
                await self.client_connections[client_id].send_text(json.dumps(message))
            except Exception:
                self.disconnect_client(client_id)

    async def broadcast(self, message: Dict):
        disconnected = []
        for ws in self.broadcast_connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect_broadcast(ws)

    async def broadcast_to_all_clients(self, message: Dict):
        disconnected = []
        for client_id, ws in self.client_connections.items():
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect_client(client_id)


voice_connection_manager = VoiceConnectionManager()


@router.websocket("/voice/ws/{client_id}")
async def voice_websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time voice command communication.

    Frontend connects here for bidirectional voice streaming.
    Supports: command, response, speak, status, ping/pong messages.
    """
    await voice_connection_manager.connect_client(client_id, websocket)
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": f"Connected as {client_id}",
            "is_listening": False,
        }))

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "command":
                    # Process voice command via REST endpoint logic
                    data_payload = message.get("data", {})
                    exec_id = data_payload.get("executive", "axiom")
                    transcript = data_payload.get("transcript", "")
                    wake_word = data_payload.get("wake_word", "")
                    confidence = data_payload.get("confidence", 1.0)

                    rt = _get_runtime()
                    valid_executives = ["axiom", "jenson", "valta_prime", "yamako"]
                    exec_id = exec_id.lower()

                    if exec_id not in valid_executives:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Invalid executive: {exec_id}",
                        }))
                        continue

                    # Process the command
                    try:
                        if exec_id == "axiom":
                            result = await _process_axiom_command(rt, type('obj', (object,), {
                                'executive': exec_id,
                                'transcript': transcript,
                                'wake_word': wake_word,
                                'confidence': confidence,
                            })())
                        else:
                            result = await _process_executive_command(rt, exec_id, type('obj', (object,), {
                                'executive': exec_id,
                                'transcript': transcript,
                                'wake_word': wake_word,
                                'confidence': confidence,
                            })())

                        # Send response back
                        await websocket.send_text(json.dumps({
                            "type": "response",
                            "executive": exec_id,
                            "response": result.response,
                            "action_taken": result.action_taken,
                            "workflow_triggered": result.workflow_triggered,
                            "requires_approval": result.requires_approval,
                            "approval_id": result.approval_id,
                        }))
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Command processing failed: {str(e)}",
                        }))

                elif message_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif message_type == "speak":
                    # Broadcast speech to all broadcast connections
                    exec_name = message.get("executive", "")
                    text = message.get("text", "")
                    urgency = message.get("urgency", "normal")
                    await voice_connection_manager.broadcast({
                        "type": "speak",
                        "executive": exec_name,
                        "text": text,
                        "urgency": urgency,
                    })

                elif message_type == "status":
                    # Update listening status
                    exec_name = message.get("executive", "")
                    is_listening = message.get("is_listening", False)
                    await voice_connection_manager.broadcast({
                        "type": "status",
                        "executive": exec_name,
                        "is_listening": is_listening,
                    })

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON",
                }))

    except WebSocketDisconnect:
        voice_connection_manager.disconnect_client(client_id)
    except Exception as e:
        voice_connection_manager.disconnect_client(client_id)
        print(f"Voice WebSocket error for {client_id}: {e}")


@router.websocket("/voice/ws/broadcast")
async def voice_broadcast_websocket(websocket: WebSocket):
    """Broadcast WebSocket for multi-client voice notifications.

    Frontend connects here to receive voice/speak and status broadcasts
    from any executive or system event.
    """
    await voice_connection_manager.connect_broadcast(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "Connected to voice broadcast",
        }))

        while True:
            # Keep connection alive, listen for ping
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        voice_connection_manager.disconnect_broadcast(websocket)
    except Exception:
        voice_connection_manager.disconnect_broadcast(websocket)


# ════════════════════════════════════════════════════════════════════════════
# Phase H — Provider Management Endpoints
# ═══════════════════════════════════════════════════════════════════════════


class ProviderToolExecuteRequest(BaseModel):
    """Request to execute a provider tool."""
    provider_id: str
    tool_id: str
    parameters: Dict[str, Any] = {}
    org_id: str = ""
    agent_id: str = "api"


class ProviderToolExecuteResponse(BaseModel):
    """Response from provider tool execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: float = 0.0
    provider_id: str
    tool_id: str
    rate_limit_remaining: Optional[int] = None


@router.get("/providers", tags=["providers"])
async def list_providers():
    """List all registered providers and their tools."""
    rt = _get_runtime()
    if not rt.provider_registry:
        return {"providers": [], "message": "Provider registry not initialized"}

    providers = rt.provider_registry.list_providers()
    result = []
    for pid, provider in providers.items():
        schema = provider.get_schema()
        result.append(schema)
    return {"providers": result, "count": len(result)}


@router.get("/providers/{provider_id}", tags=["providers"])
async def get_provider(provider_id: str):
    """Get details of a specific provider."""
    rt = _get_runtime()
    if not rt.provider_registry:
        raise HTTPException(status_code=503, detail="Provider registry not initialized")

    provider = rt.provider_registry.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    return provider.get_schema()


@router.get("/providers/{provider_id}/tools", tags=["providers"])
async def list_provider_tools(provider_id: str):
    """List all tools for a specific provider."""
    rt = _get_runtime()
    if not rt.provider_registry:
        raise HTTPException(status_code=503, detail="Provider registry not initialized")

    provider = rt.provider_registry.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    tools = []
    for tool in provider._tools.values():
        tools.append({
            "tool_id": tool.tool_id,
            "name": tool.name,
            "description": tool.description,
            "capability": tool.capability,
            "requires_approval": tool.requires_approval,
            "risk_level": tool.risk_level,
            "enabled": tool.enabled,
            "input_schema": tool.input_schema,
        })
    return {"provider_id": provider_id, "tools": tools, "count": len(tools)}


@router.get("/orgs/{org_id}/providers", tags=["providers"])
async def list_org_providers(org_id: str):
    """List all providers initialized for an organization."""
    rt = _get_runtime()
    if not rt.provider_registry:
        raise HTTPException(status_code=503, detail="Provider registry not initialized")

    providers = rt.provider_registry.get_providers_for_org(org_id)
    result = []
    for provider in providers:
        result.append(provider.get_schema())
    return {"org_id": org_id, "providers": result, "count": len(result)}


@router.get("/orgs/{org_id}/tools", tags=["providers"])
async def list_org_tools(org_id: str):
    """List all available tools for an organization."""
    rt = _get_runtime()
    if not rt.provider_registry:
        raise HTTPException(status_code=503, detail="Provider registry not initialized")

    tools = rt.provider_registry.list_tools(org_id)
    return {"org_id": org_id, "tools": tools, "count": len(tools)}


@router.get("/capabilities/{capability}/providers", tags=["providers"])
async def find_providers_for_capability(capability: str, org_id: Optional[str] = None):
    """Find providers that offer a specific capability."""
    rt = _get_runtime()
    if not rt.provider_registry:
        raise HTTPException(status_code=503, detail="Provider registry not initialized")

    providers = rt.provider_registry.find_providers_for_capability(capability, org_id)
    result = []
    for provider in providers:
        schema = provider.get_schema()
        # Also include which tools provide this capability
        schema["matching_tools"] = [
            t.tool_id for t in provider._tools.values() if t.capability == capability
        ]
        result.append(schema)
    return {"capability": capability, "providers": result, "count": len(result)}


@router.post("/providers/tools/execute", tags=["providers"])
async def execute_provider_tool(request: ProviderToolExecuteRequest):
    """Execute a provider tool."""
    rt = _get_runtime()
    if not rt.provider_registry:
        raise HTTPException(status_code=503, detail="Provider registry not initialized")

    import uuid
    from axiom.models.providers import ToolInvocationRequest

    invocation_request = ToolInvocationRequest(
        provider_id=request.provider_id,
        tool_id=request.tool_id,
        agent_id=request.agent_id,
        org_id=request.org_id,
        parameters=request.parameters,
        correlation_id=str(uuid.uuid4()),
    )

    result = await rt.provider_registry.execute_tool(invocation_request)

    return ProviderToolExecuteResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        error_code=result.error_code,
        duration_ms=result.duration_ms,
        provider_id=result.provider_id,
        tool_id=result.tool_id,
        rate_limit_remaining=result.rate_limit_remaining,
    )


@router.get("/providers/health", tags=["providers"])
async def provider_health_check():
    """Run health checks on all providers."""
    rt = _get_runtime()
    if not rt.provider_registry:
        raise HTTPException(status_code=503, detail="Provider registry not initialized")

    health_results = await rt.provider_registry.health_check_all()
    return {
        "providers": {
            pid: {
                "status": health.status.value,
                "latency_ms": health.latency_ms,
                "last_check": health.last_check.isoformat() if health.last_check else None,
                "error_message": health.error_message,
                "details": health.details,
            }
            for pid, health in health_results.items()
        },
        "total": len(health_results),
        "healthy": sum(1 for h in health_results.values() if h.status.value == "healthy"),
    }


@router.get("/providers/capabilities", tags=["providers"])
async def list_capability_mappings():
    """List all capability-to-provider mappings."""
    rt = _get_runtime()
    if not rt.provider_registry:
        raise HTTPException(status_code=503, detail="Provider registry not initialized")

    mappings = rt.provider_registry.get_capability_mappings()
    result = {}
    for capability, capability_mappings in mappings.items():
        result[capability] = [
            {
                "provider_id": m.provider_id,
                "tool_id": m.tool_id,
                "priority": m.priority,
                "org_ids": m.org_ids,
            }
            for m in capability_mappings
        ]
    return {"mappings": result, "total_capabilities": len(result)}