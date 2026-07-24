"""Pydantic models for all YAML-based configuration files.

Every config file under the organization / agent / workflow / etc. directories
has a corresponding model here.  The models are used by the registry loaders
to deserialise YAML into typed Python objects.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Organisation Models ──────────────────────────────────────────────────

class OrganizationEntry(BaseModel):
    """Entry in the top-level organizations/organization.yaml registry."""
    id: str
    name: str
    description: str
    executives: List[str]
    departments: List[str]
    enabled_tools: List[str]
    workflows: List[str]
    memory_locations: List[str]


class OrganizationRegistry(BaseModel):
    organizations: List[OrganizationEntry]


class ExecRef(BaseModel):
    id: str
    role: str
    scope: str


class DeptRef(BaseModel):
    manager: str
    agents: List[str]
    workflows: List[str]


class OrgBoundaries(BaseModel):
    can_control: List[str] = []
    cannot_control: List[str] = []
    spending_limit: float = 0.0


class MemoryAccessConfig(BaseModel):
    global_: str = Field("read", alias="global")
    organization: str = "read_write"
    departments: str = "read"
    agents: str = "read"

    model_config = ConfigDict(populate_by_name=True)


class OrgDetail(BaseModel):
    """Detailed organization definition from organizations/<id>/organization.yaml."""
    id: str
    name: str
    description: str = ""
    executives: List[ExecRef] = []
    departments: Dict[str, DeptRef] = {}
    boundaries: OrgBoundaries = OrgBoundaries()
    tools_enabled: List[str] = []
    memory_access: MemoryAccessConfig = MemoryAccessConfig()
    workflows_enabled: List[str] = []


# ── Agent Models ─────────────────────────────────────────────────────────

class AgentEntry(BaseModel):
    """Entry in the agents/agent-registry.yaml."""
    id: str
    org: str
    type: str  # "executive" | "specialist"
    department: str
    reports_to: str
    capabilities: List[str] = []


class AgentRegistry(BaseModel):
    agents: List[AgentEntry]


class CapabilityRef(BaseModel):
    id: str
    description: str = ""
    level: str = "intermediate"


class AgentMemoryConfig(BaseModel):
    enabled: bool = True
    namespace: str = ""
    persist: bool = True
    layers: Dict[str, str] = {}


class AgentToolsConfig(BaseModel):
    interfaces: List[str] = []
    subscribes_events: List[str] = []
    emits_events: List[str] = []


class AgentPermissions(BaseModel):
    can: List[str] = []
    cannot: List[str] = []


class AgentDetail(BaseModel):
    """Detailed agent definition from agents/<org>/<dept>/<agent>/agent.yml."""
    name: str
    version: str = "3.0"
    org: str = ""
    department: str = ""
    type: str = "specialist"
    reports_to: str = ""
    reports_to_type: str = "executive"
    description: str = ""
    capabilities: List[CapabilityRef] = []
    memory: AgentMemoryConfig = AgentMemoryConfig()
    knowledge: List[str] = []
    tools: AgentToolsConfig = AgentToolsConfig()
    permissions: AgentPermissions = AgentPermissions()


# ── Department Models ────────────────────────────────────────────────────

class DepartmentEntry(BaseModel):
    """Entry in the departments/departments.yaml cross-org index."""
    org: str
    id: str
    manager: str
    agents: List[str] = []
    capabilities: List[str] = []


class DepartmentRegistry(BaseModel):
    departments: List[DepartmentEntry]


class DeptAgentRef(BaseModel):
    id: str
    role: str = ""
    capabilities: List[str] = []


class MetricDef(BaseModel):
    name: str
    description: str = ""
    collection: str = ""


class DeptMemoryAccess(BaseModel):
    org_memory: str = "read"
    dept_memory: str = "read_write"
    agent_memory: str = "read"


class DepartmentDetail(BaseModel):
    """Detailed department definition from departments/<org>/<dept>/department.yaml."""
    id: str
    org: str
    manager: str
    description: str = ""
    agents: List[DeptAgentRef] = []
    workflows: List[str] = []
    metrics: List[MetricDef] = []
    memory_access: DeptMemoryAccess = DeptMemoryAccess()


# ── Workflow Models ──────────────────────────────────────────────────────

class WorkflowStep(BaseModel):
    """Step entry in the workflow-index.yaml."""
    name: str
    agent: str  # comma-separated for multi-agent steps
    action: str = ""
    output: Optional[str] = None


class WorkflowEntry(BaseModel):
    """Entry in the workflow-index.yaml."""
    description: str = ""
    org: str = ""
    department: str = ""
    coordinator: str = ""
    agents: List[str] = []
    events: List[str] = []
    trigger_event: Optional[str] = None
    steps: List[WorkflowStep] = []


class WorkflowIndex(BaseModel):
    workflows: Dict[str, WorkflowEntry]


class WorkflowDetailStep(BaseModel):
    """Step definition from individual workflow yamls."""
    id: int
    name: str = ""
    agent: str = ""
    description: str = ""
    inputs: List[str] = []
    outputs: List[str] = []
    events_emitted: List[str] = []


class WorkflowDetail(BaseModel):
    """Detailed workflow from workflows/<dept>/<name>.yaml."""
    name: str
    org: str = ""
    department: str = ""
    coordinator: str = ""
    trigger_event: Optional[str] = None
    agents: List[str] = []
    steps: List[WorkflowDetailStep] = []


# ── Executive Models ─────────────────────────────────────────────────────

class ExecutiveEntry(BaseModel):
    """Entry in core/executives.yml."""
    name: str
    domain: str = ""
    role: str = ""
    organization: str = ""


class ExecutiveRegistry(BaseModel):
    executives: List[ExecutiveEntry]


# ── Tool Models ──────────────────────────────────────────────────────────

class ToolDef(BaseModel):
    """Tool definition from organizations/<org>/tools/tools.yaml."""
    id: str
    interface: str = ""
    description: str = ""
    capabilities: List[str] = []


class ToolRegistry(BaseModel):
    tools: List[ToolDef]


# ── Capability Models ────────────────────────────────────────────────────

class CapabilityEntry(BaseModel):
    """Entry in capabilities/capability-catalog.yaml."""
    id: str
    category: str = ""
    name: str = ""
    description: str = ""
    agents: List[str] = []
    workflows: List[str] = []
    level: str = "intermediate"


class CapabilityCatalog(BaseModel):
    capabilities: List[CapabilityEntry]


class CapabilityCategory(BaseModel):
    """Category definition from capabilities/categories/*.yaml."""
    category: str = ""
    description: str = ""
    color: str = "#6366F1"
    icon: str = ""


# ── Memory Models ────────────────────────────────────────────────────────

class MemoryLayer(BaseModel):
    """Layer definition from memory/memory-index.yaml."""
    description: str = ""
    access: str = "read"
    flow: str = ""
    files: Optional[List[str]] = None
    locations: Optional[Dict[str, str]] = None
    location: Optional[str] = None


class MemoryIndex(BaseModel):
    version: str = "3.0"
    architecture: str = "layered"
    layers: Dict[str, MemoryLayer] = {}
    rules: List[str] = []