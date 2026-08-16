export const meta = {
  name: "axiom-redesign",
  description: "Complete Axiom AI OS interface redesign",
  phases: [
    { title: "Shell Architecture", detail: "TopNav, Sidebar, Dock, Layout Engine" },
    { title: "Department Workstations", detail: "AXIOM, BLEVAL, VALTA, PERSONAL, BOARDROOM" },
    { title: "System Dashboards", detail: "Settings, Home, Boardroom, Workflow" },
    { title: "Voice Integration", detail: "Central voice engine with wake words" },
    { title: "Design System", detail: "Slate tokens, reusable components" },
  ],
};

phase("Shell Architecture");

const topNav = await agent({
  prompt: "Create a new TopNavigation component at components/shell/components/TopNavigation.tsx with: Left: Axiom brand logo + System Status Badge (dynamic pill: SYSTEM ONLINE/VOICE ENGINE ACTIVE) + Global Breadcrumb. Center: Global Search Bar (Command Palette style, Cmd+K) with real-time indexing. Right: Voice Indicator (mic icon with dynamic aura animation), Telemetry Quick-Stats (CPU/GPU/Memory gauges), Profile/Active Persona Selector dropdown. Glassmorphism header: bg-slate-950/80 backdrop-blur-md border-b border-slate-800. Use existing useAxiomStore for state. Extract to reusable components: SystemStatusBadge, GlobalBreadcrumb, GlobalSearch, VoiceIndicator, TelemetryGauges, PersonaSelector",
  label: "TopNavigation",
  agentType: "general-purpose"
});

const sidebar = await agent({
  prompt: "Create a new Sidebar component at components/shell/components/Sidebar.tsx with: Collapsible Left Sidebar (w-16 collapsed / w-64 expanded) with dark glassmorphism: bg-slate-950/80 backdrop-blur-md. Navigation Nodes: Core Hub (Axiom Home, Executive Boardroom, System Settings), Workstation Departments (Operations, Engineering, Product, Marketing, Sales, Legal, Finance), Workflow & Automation (Pipeline Canvas, Agent Logs, Task Queue). Active route highlighting with left glowing accent bar (cyan-500). Dynamic tooltips on collapse using AnimatePresence. Keyboard shortcuts displayed. Use framer-motion for smooth collapse/expand transitions",
  label: "Sidebar",
  agentType: "general-purpose"
});

const shell = await agent({
  prompt: "Create a new ShellLayout component at components/shell/ShellLayout.tsx that composes: TopNavigation (fixed top, h-11 + 32px for emergency banner), Sidebar (fixed left, top-11 bottom-0), Main content area (flex-1, pt-11, ml-16 or ml-64 based on sidebar collapsed), Dock (fixed bottom, z-50), VoiceEngine (overlay), SystemTelemetry (overlay). Accepts children prop for page content. Handles boot sequence integration",
  label: "ShellLayout",
  agentType: "general-purpose"
});

await Promise.all([topNav, sidebar, shell]);

phase("Department Workstations");

const axiomWS = await agent({
  prompt: "Create AXIOMWS at components/workspace/workstations/AXIOMWS.tsx (replace existing) with: Grid-based layout (grid-cols-12) with customizable widget cards. Header: Department title, operational lead avatar, active agent count, efficiency index score. Top Row: 4 KPI cards (Active Workflows, Task Completion Rate, Agent Response Latency, Resource Allocation). Main Stage (col-span-8): Interactive workflow canvas / agent execution trees. Side Rail (col-span-4): Department metrics, recent logs, immediate action triggers. Tabs: Chat, Research, AXIOM, Board, Canvas, System, Content, Comms. Integrate InlineListeningIndicator for axiom. Slate-dark theme throughout",
  label: "AXIOMWS",
  agentType: "general-purpose"
});

const blevalWS = await agent({
  prompt: "Create BLEVALWS at components/workspace/workstations/BLEVALWS.tsx (replace existing) with: Department title: BLEVAL INC, lead: Jenson. Tabs: Overview (CommandCenter), Executives (ExecutiveBoard), Operations (OperationsCenter), Projects, Creator, Console, Intel, Comms, Content, Team, Integrations, Learning. KPI cards for operations metrics. ExecutiveBoard with real-time agent status. InlineListeningIndicator for jenson",
  label: "BLEVALWS",
  agentType: "general-purpose"
});

const valtaWS = await agent({
  prompt: "Create VALTAWS at components/workspace/workstations/VALTAWS.tsx (replace existing) with: Department title: HOUSE OF VALTA, lead: Valta Prime. Read-only market analysis banner. Tabs: Markets (TradingTerminal), Analysis, Operations, Intel, Knowledge, Content, Comms, Learning. InlineListeningIndicator for valta_prime",
  label: "VALTAWS",
  agentType: "general-purpose"
});

const personalWS = await agent({
  prompt: "Create PERSONALWS at components/workspace/workstations/PERSONALWS.tsx (replace existing) with: Department title: PERSONAL OPS, lead: Yamako. Tabs: Knowledge, Intel, Schedule, Habits, Console, Team, Integrations, Creator, Learning. HabitTracker and ScheduleView components integrated. InlineListeningIndicator for yamako",
  label: "PERSONALWS",
  agentType: "general-purpose"
});

const boardroomWS = await agent({
  prompt: "Create BOARDROOMWS at app/boardroom/page.tsx with: Virtual roundtable dashboard displaying all executive sub-agents simultaneously. Executive Cards: Modular avatar cards showing name, title, status indicator, active reasoning context, individual volume/voice metrics. Boardroom Debate/Deliberation Panel: Split-screen streaming dialogue thread where executives exchange inputs in real-time. Decision Stream / Vote Matrix: Consensus tracking panel showing alignment across executives on strategic prompts. Real-time voice activity indicators for each executive. Slate-dark theme with cyan/indigo accents",
  label: "BOARDROOMWS",
  agentType: "general-purpose"
});

await Promise.all([axiomWS, blevalWS, valtaWS, personalWS, boardroomWS]);

phase("System Dashboards");

const settingsDash = await agent({
  prompt: "Create SettingsDashboard at app/settings/page.tsx with: Dual-pane view: categories on left, interactive controls on right. Categories: Voice Engine, AI Models, System Resources, Integrations, Security, Appearance. Live Analytics Section: Dynamic line/area charts (Recharts) tracking voice pipeline latency, system throughput, memory leaks, token consumption over time. Controls & Sliders: Voice Sensitivity, Wake Word Thresholds, LLM Temperature, Sub-Agent Concurrency Limits. Tool Configuration Cards: Grid displaying active integrations (APIs, Databases, Memory Stores) with status toggles and latency indicators. Slate-dark theme, glassmorphism cards",
  label: "SettingsDashboard",
  agentType: "general-purpose"
});

const homeDash = await agent({
  prompt: "Create HomeDashboard at app/page.tsx (replace existing) with: Hero Section: Command prompt input supporting both voice stream audio visualizer and text input, flanked by high-level system readiness status. Executive Summary Grid: Cards for each C-Suite agent (CTO/Jenson, CMO, CFO/Valta Prime, COO/Yamako) with active status, current task execution, quick-call voice buttons. Activity Stream: Real-time event log highlighting system decisions, automated task approvals, cross-agent communications. Central command overview for executive multi-agent oversight. Slate-dark theme",
  label: "HomeDashboard",
  agentType: "general-purpose"
});

const workflowWS = await agent({
  prompt: "Create WorkflowWorkstation at app/axiom/workflow/page.tsx with: Canvas-first workspace with node-based pipeline routing. Node Graph Editor: Visual node-based workflow builder (Trigger -> Processing Agent -> Review Executive -> Output Action) using React Flow or custom implementation. Execution Panel: Live debugging panel showing node execution time, variable outputs, failure recovery logs. Template Drawer: Slide-over drawer for dragging pre-built workflow templates onto canvas. Slate-dark theme",
  label: "WorkflowWorkstation",
  agentType: "general-purpose"
});

await Promise.all([settingsDash, homeDash, workflowWS]);

phase("Voice Integration");

const voiceIntegration = await agent({
  prompt: "Update VoiceEngine at components/axiom/VoiceEngine.tsx and create ListeningIndicator components: Wake Word Activation: Each executive monitors for their name (Axiom, Jenson, Valta Prime, Yamako). State transitions: IDLE -> LISTENING -> PROCESSING -> SPEAKING. Workstation UI Listening Indicator: Every executive card + top navbar renders interactive Listening Status Indicator with pulsing aura / audio-reactive wave animation. Voice-In/Voice-Out Pipeline: STT -> Target Executive -> TTS with unique voice profiles per agent. Create InlineListeningIndicator at components/ListeningIndicator.tsx (enhance existing). Create GlobalListeningIndicator for TopNavigation. Integrate with useVoiceWebSocket for real-time communication",
  label: "VoiceIntegration",
  agentType: "general-purpose"
});

const listeningIndicators = await agent({
  prompt: "Create/Update ListeningIndicator components: InlineListeningIndicator at components/ListeningIndicator.tsx: Small indicator for executive cards (pulsing dot + wave animation). GlobalListeningIndicator at components/shell/components/GlobalListeningIndicator.tsx: Large indicator for TopNavigation with audio-reactive visualization. ExecutiveCardListeningIndicator: For Boardroom executive cards with volume/voice metrics. All use framer-motion animate-breathe and animate-waveform animations. Colors: cyan-500 for listening, green-500 for processing, indigo-500 for speaking",
  label: "ListeningIndicators",
  agentType: "general-purpose"
});

await Promise.all([voiceIntegration, listeningIndicators]);

phase("Design System");

const designTokens = await agent({
  prompt: "Update globals.css with complete slate-based design system: Palette: slate-950 backgrounds, slate-900 card fills, slate-800 borders, cyan-500/indigo-500 glowing accents. CSS Variables for all colors, shadows, radii, transitions. Dark mode only (light mode removed). Glassmorphism utilities: .glass-panel, .glass-card, .glass-panel-light. Button variants: .axiom-btn-primary, .axiom-btn-secondary, .axiom-btn-ghost, .axiom-btn-danger. Input, Label, Card, Badge, Separator, Tooltip, Dropdown, Avatar, Status, Tab, KBD, ScrollArea primitives. Animation keyframes: waveform, breathe, float, pulse, shimmer, slide, scale. All utility classes for responsive behavior",
  label: "DesignTokens",
  agentType: "general-purpose"
});

const reusableComponents = await agent({
  prompt: "Create reusable component library at components/shell/components/: MetricCard.tsx, ExecutiveCard.tsx, ListeningIndicator.tsx, StatusBadge.tsx, TelemetryGauge.tsx, Breadcrumb.tsx, SearchBar.tsx, PersonaSelector.tsx, VoiceVisualizer.tsx, NodeCard.tsx, TemplateCard.tsx. All using slate-dark theme, glassmorphism, framer-motion animations",
  label: "ReusableComponents",
  agentType: "general-purpose"
});

await Promise.all([designTokens, reusableComponents]);

log("Axiom AI OS Redesign Complete!");
return { status: "complete" };