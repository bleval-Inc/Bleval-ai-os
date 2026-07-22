"""Axiom OS CLI — command-line interface for interacting with the runtime.

Usage:
    python -m axiom.cli.main status         # Show runtime status
    python -m axiom.cli.main workflows       # List all workflows
    python -m axiom.cli.main launch <id>     # Launch a workflow
    python -m axiom.cli.main agents          # List all agents
    python -m axiom.cli.main organisations   # List organisations
    python -m axiom.cli.main capabilities    # List capabilities
    python -m axiom.cli.main search <query>  # Search for capabilities
    python -m axiom.cli.main events          # List event types
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import typer

from axiom.runtime.lifecycle import AxiomRuntime

app = typer.Typer(help="Axiom OS — AI Operating System CLI")

# Global runtime instance
_runtime = AxiomRuntime()


def _sync_run(coro):
    """Run an async function synchronously."""
    return asyncio.run(coro)


def _print_json(data: Any) -> None:
    """Pretty-print data as JSON."""
    print(json.dumps(data, indent=2, default=str))


@app.callback()
def callback():
    """Axiom OS CLI — interact with the runtime."""


@app.command()
def status():
    """Show runtime status and component health."""
    rt = _sync_run(_bootstrap_and_get())
    info = rt.get_summary()
    _print_json(info)


@app.command()
def workflows():
    """List all defined workflows."""
    rt = _sync_run(_bootstrap_and_get())
    wf_list = [
        {"id": wf_id, "org": wf.org, "department": wf.department,
         "steps": len(wf.steps), "trigger": wf.trigger_event}
        for wf_id, wf in rt.workflow.list_workflows().items()
    ]
    _print_json(wf_list)


@app.command()
def launch(workflow_id: str, context: Optional[str] = None):
    """Launch a workflow instance."""
    rt = _sync_run(_bootstrap_and_get())
    ctx = json.loads(context) if context else {}
    instance = rt.workflow.create_instance(workflow_id, ctx)
    _sync_run(rt.workflow.start(instance.instance_id))
    print(f"Launched workflow: {workflow_id}")
    print(f"Instance ID: {instance.instance_id}")
    print(f"Status: {instance.status.value}")


@app.command()
def instances(status_filter: Optional[str] = None):
    """List workflow instances."""
    rt = _sync_run(_bootstrap_and_get())
    insts = rt.workflow.list_instances()
    if status_filter:
        from axiom.models.workflows import WorkflowStatus
        insts = [i for i in insts if i.status.value == status_filter]
    data = [
        {"instance_id": i.instance_id, "workflow_id": i.workflow_id,
         "status": i.status.value, "steps": len(i.steps),
         "current_step": i.current_step_index}
        for i in insts
    ]
    _print_json(data)


@app.command()
def advance(instance_id: str):
    """Advance a workflow instance to the next step."""
    rt = _sync_run(_bootstrap_and_get())
    running = _sync_run(rt.workflow.advance(instance_id))
    inst = rt.workflow.get_instance(instance_id)
    print(f"Instance: {instance_id}")
    print(f"Status: {inst.status.value}")
    print(f"Running: {running}")


@app.command()
def agents():
    """List all registered agents."""
    rt = _sync_run(_bootstrap_and_get())
    agent_list = [
        {"id": a.id, "org": a.org, "department": a.department, "type": a.type}
        for a in rt.executive.list_all_agents()
    ]
    _print_json(agent_list)


@app.command()
def organisations():
    """List all organisations."""
    rt = _sync_run(_bootstrap_and_get())
    orgs = [
        {"id": o.id, "name": o.name, "executives": o.executives,
         "departments": len(o.departments), "workflows": len(o.workflows)}
        for o in rt.executive.list_organizations()
    ]
    _print_json(orgs)


@app.command()
def capabilities(search_query: Optional[str] = None):
    """List capabilities, optionally filtered by search query."""
    rt = _sync_run(_bootstrap_and_get())
    if search_query:
        caps = rt.executive.search_capabilities(search_query)
    else:
        caps = rt.executive.list_capabilities()
    data = [
        {"id": c.id, "category": c.category, "name": c.name,
         "level": c.level, "agents": c.agents}
        for c in caps
    ]
    _print_json(data)


@app.command()
def events():
    """List all registered event types."""
    rt = _sync_run(_bootstrap_and_get())
    evts = [
        {"name": name, "channel": et.channel, "description": et.description,
         "emitters": et.emitted_by, "subscribers": et.subscribed_by}
        for name, et in rt.event.list_event_types().items()
    ]
    _print_json(evts)


@app.command()
def memory(agent_id: str, org: str = "", dept: str = ""):
    """Get resolved memory context for an agent."""
    rt = _sync_run(_bootstrap_and_get())
    ctx = rt.memory.get_resolved_context(agent_id, org, dept)
    data = {"agent_id": agent_id, "files": list(ctx.keys()), "total_chars": len(str(ctx))}
    _print_json(data)


@app.command()
def health():
    """Show system health."""
    rt = _sync_run(_bootstrap_and_get())
    _print_json(rt.monitor.get_summary())


async def _bootstrap_and_get() -> AxiomRuntime:
    """Ensure the runtime is initialised and return it."""
    await _runtime.bootstrap()
    # Note: start() starts background tasks (event processor, scheduler, etc.)
    # For CLI mode we bootstrap only — the runtime is operational for queries
    return _runtime


if __name__ == "__main__":
    app()