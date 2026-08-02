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