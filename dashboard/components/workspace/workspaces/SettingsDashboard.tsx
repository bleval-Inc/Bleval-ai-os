"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore } from "../../../lib/store/axiom-store";
import { system, axiom as axiomApi, voice as voiceApi, executives as execApi } from "../../../lib/api";
import { cn } from "../../../lib/utils";
import type { RuntimeStatus, HealthSummary, ExecutiveBoardStatus } from "../../../lib/api-types";

const SETTINGS_CATEGORIES = [
  { id: "voice", label: "Voice Engine", icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="8" y1="22" x2="16" y2="22" />
    </svg>
  )},
  { id: "llm", label: "LLM Parameters", icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4Z" />
      <path d="M2 22v-2a6 6 0 0 1 6-6h8a6 6 0 0 1 6 6v2" />
    </svg>
  )},
  { id: "agents", label: "Agent Concurrency", icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )},
  { id: "telemetry", label: "Telemetry & Analytics", icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )},
  { id: "integrations", label: "Integrations", icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
    </svg>
  )},
  { id: "system", label: "System", icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
    </svg>
  )},
] as const;

type SettingsCategory = typeof SETTINGS_CATEGORIES[number]["id"];

interface SliderConfig {
  id?: string;
  label: string;
  description?: string;
  min: number;
  max: number;
  step: number;
  value: number;
  unit?: string;
  category?: SettingsCategory;
  onChange: (value: number) => void;
}

interface ToggleConfig {
  id?: string;
  label: string;
  description?: string;
  value: boolean;
  category?: SettingsCategory;
  onChange: (value: boolean) => void;
}

interface IntegrationConfig {
  id: string;
  name: string;
  type: "api" | "database" | "memory" | "service";
  status: "connected" | "disconnected" | "error" | "pending";
  latency?: number;
  description: string;
  onToggle: (value: boolean) => void;
}

export default function SettingsDashboard() {
  const { setActiveWorkstationView } = useAxiomStore();
  const [activeCategory, setActiveCategory] = useState<SettingsCategory>("voice");
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [health, setHealth] = useState<HealthSummary | null>(null);
  const [executives, setExecutives] = useState<ExecutiveBoardStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // Voice Engine Settings
  const [voiceSettings, setVoiceSettings] = useState({
    awake: true,
    sensitivity: 0.7,
    wakeWordThreshold: 0.6,
    voiceVADThreshold: 0.5,
    noiseSuppression: 0.8,
    autoGainControl: 0.9,
    echoCancellation: true,
    continuousListening: true,
    voiceProfiles: {
      axiom: { voice: "nova", speed: 1.0, pitch: 1.0 },
      jenson: { voice: "onyx", speed: 1.1, pitch: 0.9 },
      valta_prime: { voice: "echo", speed: 0.95, pitch: 1.0 },
      yamako: { voice: "shimmer", speed: 1.05, pitch: 1.1 },
    },
  });

  // LLM Parameters
  const [llmSettings, setLlmSettings] = useState({
    temperature: 0.7,
    topP: 0.9,
    topK: 40,
    maxTokens: 4096,
    presencePenalty: 0.1,
    frequencyPenalty: 0.1,
    reasoningDepth: 3,
    contextWindow: 128000,
    streamingEnabled: true,
    cacheEnabled: true,
  });

  // Agent Concurrency
  const [agentSettings, setAgentSettings] = useState({
    maxConcurrentAgents: 8,
    maxConcurrentWorkflows: 4,
    subAgentTimeout: 30000,
    queueDepth: 50,
    priorityQueueEnabled: true,
    autoScaleEnabled: true,
    minIdleAgents: 2,
    taskRetryLimit: 3,
  });

  // Telemetry
  const [telemetrySettings, setTelemetrySettings] = useState({
    cpuMonitoring: true,
    memoryMonitoring: true,
    diskMonitoring: true,
    networkMonitoring: true,
    gpuMonitoring: false,
    voiceLatencyTracking: true,
    tokenConsumptionTracking: true,
    workflowExecutionTracking: true,
    alertThresholds: {
      cpu: 80,
      memory: 85,
      disk: 90,
      voiceLatency: 500,
    },
    samplingRate: 5000,
    retentionDays: 30,
  });

  // Integrations
  const [integrations, setIntegrations] = useState<IntegrationConfig[]>([
    { id: "anthropic", name: "Anthropic API", type: "api", status: "connected", latency: 42, description: "Claude models access", onToggle: () => {} },
    { id: "openai", name: "OpenAI API", type: "api", status: "connected", latency: 38, description: "GPT models access", onToggle: () => {} },
    { id: "elevenlabs", name: "ElevenLabs TTS", type: "api", status: "connected", latency: 65, description: "Voice synthesis", onToggle: () => {} },
    { id: "supabase", name: "Supabase", type: "database", status: "connected", latency: 12, description: "PostgreSQL + Realtime", onToggle: () => {} },
    { id: "redis", name: "Redis Cache", type: "database", status: "connected", latency: 3, description: "Session & queue caching", onToggle: () => {} },
    { id: "pinecone", name: "Pinecone Vector DB", type: "memory", status: "connected", latency: 28, description: "Semantic memory store", onToggle: () => {} },
    { id: "qdrant", name: "Qdrant Local", type: "memory", status: "disconnected", description: "Local vector search", onToggle: () => {} },
    { id: "github", name: "GitHub API", type: "api", status: "connected", latency: 85, description: "Repository management", onToggle: () => {} },
    { id: "slack", name: "Slack Bot", type: "service", status: "pending", description: "Team notifications", onToggle: () => {} },
    { id: "vercel", name: "Vercel Deploy", type: "service", status: "connected", latency: 120, description: "Preview deployments", onToggle: () => {} },
  ]);

  // System settings
  const [systemSettings, setSystemSettings] = useState({
    autoBoot: true,
    bootVerbose: false,
    debugMode: false,
    telemetryEnabled: true,
    crashReporting: true,
    autoUpdate: false,
    maintenanceWindow: "03:00-05:00",
    logLevel: "info",
    dataRetention: 90,
    encryptionAtRest: true,
    sessionTimeout: 480,
  });

  // Fetch system data
  const fetchData = useCallback(async () => {
    try {
      const [rt, execs] = await Promise.all([
        system.getRuntimeStatus().catch(() => null),
        execApi.boardStatus().catch(() => null),
      ]);
      setRuntime(rt);
      if (rt?.health) setHealth(rt.health);
      if (execs) setExecutives(execs);
    } catch {
      // silent fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Voice settings handlers
  const updateVoiceSetting = (key: string, value: any) => {
    setVoiceSettings(prev => ({ ...prev, [key]: value }));
  };

  const updateSlideSetting = (key: string, value: number) => {
    if (key.includes(".")) {
      const [execId, child] = key.split(".");
      setVoiceSettings(prev => ({
        ...prev,
        voiceProfiles: {
          ...prev.voiceProfiles,
          [execId]: { ...prev.voiceProfiles[execId as keyof typeof prev.voiceProfiles], [child]: value },
        },
      }));
    }
  };

  // LLM settings handlers
  const updateLlmSetting = (key: string, value: any) => {
    setLlmSettings(prev => ({ ...prev, [key]: value }));
  };

  // Agent settings handlers
  const updateAgentSetting = (key: string, value: any) => {
    setAgentSettings(prev => ({ ...prev, [key]: value }));
  };

  // Telemetry handlers
  const updateTelemetrySetting = (key: string, value: any) => {
    if (key.includes(".")) {
      const [parent, child] = key.split(".");
      setTelemetrySettings(prev => ({
        ...prev,
        [parent]: { ...(prev as any)[parent], [child]: value },
      }));
    } else {
      setTelemetrySettings(prev => ({ ...prev, [key]: value }));
    }
  };

  // Integration handlers
  const toggleIntegration = (id: string, enabled: boolean) => {
    setIntegrations(prev => prev.map(i => i.id === id ? { ...i, status: enabled ? "connected" : "disconnected" } : i));
  };

  // System handlers
  const updateSystemSetting = (key: string, value: any) => {
    setSystemSettings(prev => ({ ...prev, [key]: value }));
  };

  const renderCategoryContent = () => {
    switch (activeCategory) {
      case "voice":
        return renderVoiceSettings();
      case "llm":
        return renderLLMSettings();
      case "agents":
        return renderAgentSettings();
      case "telemetry":
        return renderTelemetrySettings();
      case "integrations":
        return renderIntegrationsSettings();
      case "system":
        return renderSystemSettings();
      default:
        return null;
    }
  };

  function renderVoiceSettings() {
    return (
      <div className="space-y-6">
        {/* Voice Engine Status */}
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${voiceSettings.awake ? "bg-emerald-400" : "bg-slate-500"}`} />
            Voice Engine Status
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Slider
              label="Wake Word Sensitivity"
              description="Threshold for detecting wake words"
              value={voiceSettings.sensitivity}
              min={0.1}
              max={1}
              step={0.05}
              onChange={v => updateVoiceSetting("sensitivity", v)}
              unit=""
            />
            <Slider
              label="Wake Word Threshold"
              description="Confidence required to trigger"
              value={voiceSettings.wakeWordThreshold}
              min={0.1}
              max={1}
              step={0.05}
              onChange={v => updateVoiceSetting("wakeWordThreshold", v)}
              unit=""
            />
            <Slider
              label="VAD Threshold"
              description="Voice Activity Detection sensitivity"
              value={voiceSettings.voiceVADThreshold}
              min={0.1}
              max={1}
              step={0.05}
              onChange={v => updateVoiceSetting("voiceVADThreshold", v)}
              unit=""
            />
          </div>
        </div>

        {/* Audio Processing */}
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Audio Processing</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Slider
              label="Noise Suppression"
              description="Background noise reduction level"
              value={voiceSettings.noiseSuppression}
              min={0}
              max={1}
              step={0.05}
              onChange={v => updateVoiceSetting("noiseSuppression", v)}
              unit=""
            />
            <Slider
              label="Auto Gain Control"
              description="Automatic microphone gain adjustment"
              value={voiceSettings.autoGainControl}
              min={0}
              max={1}
              step={0.05}
              onChange={v => updateVoiceSetting("autoGainControl", v)}
              unit=""
            />
            <Toggle
              label="Echo Cancellation"
              description="Remove audio feedback from speakers"
              value={voiceSettings.echoCancellation}
              onChange={v => updateVoiceSetting("echoCancellation", v)}
            />
            <Toggle
              label="Continuous Listening"
              description="Always listen for wake words"
              value={voiceSettings.continuousListening}
              onChange={v => updateVoiceSetting("continuousListening", v)}
            />
          </div>
        </div>

        {/* Voice Profiles */}
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Executive Voice Profiles</h3>
          <div className="space-y-3">
            {Object.entries(voiceSettings.voiceProfiles).map(([execId, profile]) => (
              <div key={execId} className="flex items-center gap-3 p-3 rounded-lg bg-white/2.5 border border-white/5">
                <div className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br",
                  execId === "axiom" ? "from-indigo-400 to-indigo-600" :
                  execId === "jenson" ? "from-blue-400 to-blue-600" :
                  execId === "valta_prime" ? "from-amber-400 to-amber-600" : "from-violet-400 to-violet-600"
                )}>
                  <span className="text-xs font-bold text-white">{execId.charAt(0).toUpperCase()}</span>
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-white capitalize">{execId.replace("_", " ")}</div>
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>Voice: {profile.voice}</span>
                    <span>Speed: {profile.speed}x</span>
                    <span>Pitch: {profile.pitch}x</span>
                  </div>
                </div>
                <Slider
                  label="Speed"
                  value={profile.speed}
                  min={0.5}
                  max={2}
                  step={0.05}
                  onChange={v => updateSlideSetting(`${execId}.speed`, v)}
                  unit="x"
                />
                <Slider
                  label="Pitch"
                  value={profile.pitch}
                  min={0.5}
                  max={2}
                  step={0.05}
                  onChange={v => updateSlideSetting(`${execId}.pitch`, v)}
                  unit="x"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Master Toggle */}
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <Toggle
            label="Voice Engine Active"
            description="Enable/disable the entire voice system"
            value={voiceSettings.awake}
            onChange={v => updateVoiceSetting("awake", v)}
          />
        </div>
      </div>
    );
  }

  function renderLLMSettings() {
    return (
      <div className="space-y-6">
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Model Parameters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Slider
              label="Temperature"
              description="Controls randomness in outputs"
              value={llmSettings.temperature}
              min={0}
              max={2}
              step={0.1}
              onChange={v => updateLlmSetting("temperature", v)}
              unit=""
            />
            <Slider
              label="Top-P"
              description="Nucleus sampling threshold"
              value={llmSettings.topP}
              min={0}
              max={1}
              step={0.05}
              onChange={v => updateLlmSetting("topP", v)}
              unit=""
            />
            <Slider
              label="Top-K"
              description="Top-k sampling limit"
              value={llmSettings.topK}
              min={1}
              max={100}
              step={1}
              onChange={v => updateLlmSetting("topK", v)}
              unit=""
            />
            <Slider
              label="Max Tokens"
              description="Maximum response length"
              value={llmSettings.maxTokens}
              min={512}
              max={8192}
              step={256}
              onChange={v => updateLlmSetting("maxTokens", v)}
              unit=" tokens"
            />
            <Slider
              label="Presence Penalty"
              description="Encourages new topics"
              value={llmSettings.presencePenalty}
              min={-2}
              max={2}
              step={0.1}
              onChange={v => updateLlmSetting("presencePenalty", v)}
              unit=""
            />
            <Slider
              label="Frequency Penalty"
              description="Reduces repetition"
              value={llmSettings.frequencyPenalty}
              min={-2}
              max={2}
              step={0.1}
              onChange={v => updateLlmSetting("frequencyPenalty", v)}
              unit=""
            />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Advanced Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Slider
              label="Reasoning Depth"
              description="Number of reasoning iterations"
              value={llmSettings.reasoningDepth}
              min={1}
              max={10}
              step={1}
              onChange={v => updateLlmSetting("reasoningDepth", v)}
              unit=""
            />
            <Slider
              label="Context Window"
              description="Maximum context tokens"
              value={llmSettings.contextWindow}
              min={4096}
              max={200000}
              step={4096}
              onChange={v => updateLlmSetting("contextWindow", v)}
              unit="k"
            />
            <Toggle
              label="Streaming Enabled"
              description="Stream responses token-by-token"
              value={llmSettings.streamingEnabled}
              onChange={v => updateLlmSetting("streamingEnabled", v)}
            />
            <Toggle
              label="Cache Enabled"
              description="Cache repeated prompts"
              value={llmSettings.cacheEnabled}
              onChange={v => updateLlmSetting("cacheEnabled", v)}
            />
          </div>
        </div>
      </div>
    );
  }

  function renderAgentSettings() {
    return (
      <div className="space-y-6">
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Concurrency Limits</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Slider
              label="Max Concurrent Agents"
              value={agentSettings.maxConcurrentAgents}
              min={1}
              max={20}
              step={1}
              onChange={v => updateAgentSetting("maxConcurrentAgents", v)}
              unit=""
            />
            <Slider
              label="Max Concurrent Workflows"
              value={agentSettings.maxConcurrentWorkflows}
              min={1}
              max={10}
              step={1}
              onChange={v => updateAgentSetting("maxConcurrentWorkflows", v)}
              unit=""
            />
            <Slider
              label="Sub-Agent Timeout (ms)"
              value={agentSettings.subAgentTimeout}
              min={5000}
              max={120000}
              step={5000}
              onChange={v => updateAgentSetting("subAgentTimeout", v)}
              unit="ms"
            />
            <Slider
              label="Queue Depth"
              value={agentSettings.queueDepth}
              min={10}
              max={200}
              step={10}
              onChange={v => updateAgentSetting("queueDepth", v)}
              unit=""
            />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Behavior Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Toggle
              label="Priority Queue Enabled"
              description="Process high-priority tasks first"
              value={agentSettings.priorityQueueEnabled}
              onChange={v => updateAgentSetting("priorityQueueEnabled", v)}
            />
            <Toggle
              label="Auto-Scale Enabled"
              description="Automatically scale agent pool based on load"
              value={agentSettings.autoScaleEnabled}
              onChange={v => updateAgentSetting("autoScaleEnabled", v)}
            />
            <Slider
              label="Min Idle Agents"
              value={agentSettings.minIdleAgents}
              min={0}
              max={5}
              step={1}
              onChange={v => updateAgentSetting("minIdleAgents", v)}
              unit=""
            />
            <Slider
              label="Task Retry Limit"
              value={agentSettings.taskRetryLimit}
              min={0}
              max={10}
              step={1}
              onChange={v => updateAgentSetting("taskRetryLimit", v)}
              unit=""
            />
          </div>
        </div>

        {/* Live Metrics */}
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Live Agent Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricDisplay label="Running Agents" value={executives ? Object.values(executives).filter(e => e.status === "running").length : 0} />
            <MetricDisplay label="Stopped Agents" value={executives ? Object.values(executives).filter(e => e.status === "stopped").length : 0} />
            <MetricDisplay label="Error Agents" value={executives ? Object.values(executives).filter(e => e.status === "error").length : 0} />
            <MetricDisplay label="Total Agents" value={executives ? Object.values(executives).length : 0} />
          </div>
        </div>
      </div>
    );
  }

  function renderTelemetrySettings() {
    const healthScore = health?.overall === "healthy" ? Math.round(100 - health.unhealthy * 12) : Math.max(30, Math.round(80 - (health?.unhealthy ?? 0) * 20));
    const activeWorkflows = runtime?.workflows_defined ?? 0;
    return (
      <div className="space-y-6">
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Monitoring Modules</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { key: "cpuMonitoring", label: "CPU Monitoring", desc: "Track processor utilization" },
              { key: "memoryMonitoring", label: "Memory Monitoring", desc: "Track RAM usage" },
              { key: "diskMonitoring", label: "Disk Monitoring", desc: "Track storage usage" },
              { key: "networkMonitoring", label: "Network Monitoring", desc: "Track I/O throughput" },
              { key: "gpuMonitoring", label: "GPU Monitoring", desc: "Track GPU utilization (if available)" },
              { key: "voiceLatencyTracking", label: "Voice Latency", desc: "Track STT/TTS pipeline latency" },
              { key: "tokenConsumptionTracking", label: "Token Consumption", desc: "Track LLM token usage" },
              { key: "workflowExecutionTracking", label: "Workflow Tracking", desc: "Track workflow execution metrics" },
            ].map(item => (
              <Toggle
                key={item.key}
                label={item.label}
                description={item.desc}
                value={telemetrySettings[item.key as keyof typeof telemetrySettings] as boolean}
                onChange={v => updateTelemetrySetting(item.key, v)}
              />
            ))}
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Alert Thresholds</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Slider
              label="CPU Alert %"
              value={telemetrySettings.alertThresholds.cpu}
              min={50}
              max={95}
              step={5}
              onChange={v => updateTelemetrySetting("alertThresholds.cpu", v)}
              unit="%"
            />
            <Slider
              label="Memory Alert %"
              value={telemetrySettings.alertThresholds.memory}
              min={50}
              max={95}
              step={5}
              onChange={v => updateTelemetrySetting("alertThresholds.memory", v)}
              unit="%"
            />
            <Slider
              label="Disk Alert %"
              value={telemetrySettings.alertThresholds.disk}
              min={70}
              max={99}
              step={1}
              onChange={v => updateTelemetrySetting("alertThresholds.disk", v)}
              unit="%"
            />
            <Slider
              label="Voice Latency Alert (ms)"
              value={telemetrySettings.alertThresholds.voiceLatency}
              min={100}
              max={2000}
              step={50}
              onChange={v => updateTelemetrySetting("alertThresholds.voiceLatency", v)}
              unit="ms"
            />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Data Collection</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Slider
              label="Sampling Rate (ms)"
              value={telemetrySettings.samplingRate}
              min={1000}
              max={60000}
              step={1000}
              onChange={v => updateTelemetrySetting("samplingRate", v)}
              unit="ms"
            />
            <Slider
              label="Retention (days)"
              value={telemetrySettings.retentionDays}
              min={1}
              max={365}
              step={1}
              onChange={v => updateTelemetrySetting("retentionDays", v)}
              unit=" days"
            />
          </div>
        </div>
      </div>
    );
  }

  function renderIntegrationsSettings() {
    return (
      <div className="space-y-6">
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Configured Integrations</h3>
          <div className="space-y-2">
            {integrations.map(integration => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onToggle={toggleIntegration}
              />
            ))}
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Add Integration</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <AddIntegrationButton type="api" label="Add API" desc="REST/GraphQL endpoints" />
            <AddIntegrationButton type="database" label="Add Database" desc="PostgreSQL, MySQL, etc." />
            <AddIntegrationButton type="memory" label="Add Memory Store" desc="Vector databases, caches" />
          </div>
        </div>
      </div>
    );
  }

  function renderSystemSettings() {
    return (
      <div className="space-y-6">
        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Boot & Runtime</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Toggle
              label="Auto Boot"
              description="Start system automatically on launch"
              value={systemSettings.autoBoot}
              onChange={v => updateSystemSetting("autoBoot", v)}
            />
            <Toggle
              label="Verbose Boot"
              description="Show detailed boot sequence logs"
              value={systemSettings.bootVerbose}
              onChange={v => updateSystemSetting("bootVerbose", v)}
            />
            <Toggle
              label="Debug Mode"
              description="Enable debug logging and inspector"
              value={systemSettings.debugMode}
              onChange={v => updateSystemSetting("debugMode", v)}
            />
            <Toggle
              label="Telemetry Enabled"
              description="Collect and display system metrics"
              value={systemSettings.telemetryEnabled}
              onChange={v => updateSystemSetting("telemetryEnabled", v)}
            />
            <Toggle
              label="Crash Reporting"
              description="Send anonymous crash reports"
              value={systemSettings.crashReporting}
              onChange={v => updateSystemSetting("crashReporting", v)}
            />
            <Toggle
              label="Auto Update"
              description="Automatically apply updates"
              value={systemSettings.autoUpdate}
              onChange={v => updateSystemSetting("autoUpdate", v)}
            />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">Maintenance & Security</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-xs text-slate-500 uppercase tracking-wider">Maintenance Window</label>
              <input
                type="text"
                value={systemSettings.maintenanceWindow}
                onChange={e => updateSystemSetting("maintenanceWindow", e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500"
                placeholder="HH:MM-HH:MM"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-xs text-slate-500 uppercase tracking-wider">Log Level</label>
              <select
                value={systemSettings.logLevel}
                onChange={e => updateSystemSetting("logLevel", e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
              >
                <option value="debug">Debug</option>
                <option value="info">Info</option>
                <option value="warn">Warn</option>
                <option value="error">Error</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="block text-xs text-slate-500 uppercase tracking-wider">Data Retention (days)</label>
              <input
                type="number"
                value={systemSettings.dataRetention}
                onChange={e => updateSystemSetting("dataRetention", parseInt(e.target.value))}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500"
                min="1"
                max="365"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-xs text-slate-500 uppercase tracking-wider">Session Timeout (min)</label>
              <input
                type="number"
                value={systemSettings.sessionTimeout}
                onChange={e => updateSystemSetting("sessionTimeout", parseInt(e.target.value))}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500"
                min="30"
                max="1440"
              />
            </div>
            <Toggle
              label="Encryption at Rest"
              description="Encrypt stored data"
              value={systemSettings.encryptionAtRest}
              onChange={v => updateSystemSetting("encryptionAtRest", v)}
            />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-white mb-4">System Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              {runtime && [
                { label: "Version", value: runtime.version },
                { label: "Status", value: runtime.running ? "Running" : "Stopped" },
                { label: "Initialized", value: runtime.initialised ? "Yes" : "No" },
                { label: "Workflows", value: runtime.workflows_defined.toString() },
                { label: "Executives", value: runtime.executives.toString() },
                { label: "Organizations", value: runtime.org_count.toString() },
              ].map(item => (
                <div key={item.label} className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">{item.label}</span>
                  <span className="font-mono text-white">{item.value}</span>
                </div>
              ))}
            </div>
            <div className="space-y-2">
              {runtime && Object.entries(runtime.components ?? {}).map(([name, active]) => (
                <div key={name} className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400 capitalize">{name.replace(/_/g, " ")}</span>
                  <span className="font-mono text-white">{active ? "Active" : "Inactive"}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex h-full overflow-hidden">
      {/* Left Sidebar - Categories */}
      <aside className={cn(
        "w-64 flex flex-col bg-[var(--axiom-bg-surface)]/70 backdrop-blur-xl border-r border-white/5",
        "transition-all duration-300",
        !isPanelOpen && "w-16"
      )}>
        <div className="p-4 border-b border-white/5">
          <h2 className={cn("font-semibold text-white", !isPanelOpen && "hidden")}>Settings</h2>
        </div>
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {SETTINGS_CATEGORIES.map(cat => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950",
                activeCategory === cat.id
                  ? "bg-indigo-500/10 text-indigo-400"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
              )}
            >
              <span className="flex-shrink-0">{cat.icon}</span>
              <span className={cn("font-medium", !isPanelOpen && "hidden")}>{cat.label}</span>
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-white/5">
          <button
            onClick={() => setIsPanelOpen(!isPanelOpen)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points={isPanelOpen ? "15 18 9 12 15 6" : "9 18 15 12 9 6"} />
            </svg>
            <span className={cn("text-xs font-medium", !isPanelOpen && "hidden")}>
              {isPanelOpen ? "Collapse" : "Expand"}
            </span>
          </button>
        </div>
      </aside>

      {/* Right Panel - Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-white/2.5 backdrop-blur-sm">
          <h1 className="text-lg font-semibold text-white">System Settings & Telemetry</h1>
          <div className="flex items-center gap-3">
            <span className={`w-2 h-2 rounded-full ${runtime?.running ? "bg-emerald-400" : "bg-rose-400"}`} />
            <span className="text-sm text-slate-400">{runtime?.running ? "System Online" : "System Offline"}</span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex gap-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="w-2 h-2 rounded-full bg-indigo-400 animate-dot-pulse" style={{ animationDelay: `${i * 150}ms` }} />
                ))}
              </div>
            </div>
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={activeCategory}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className="h-full"
              >
                {renderCategoryContent()}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </main>
    </div>
  );
}

// ── Reusable UI Components ────────────────────────────────────────────────

function Slider({ label, description, value, min, max, step, onChange, unit = "", category }: SliderConfig) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <div>
          <label className="text-sm font-medium text-white">{label}</label>
          <p className="text-xs text-slate-500">{description}</p>
        </div>
        <span className="text-sm font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-white/5 rounded-lg appearance-none accent-indigo-400 cursor-pointer"
      />
    </div>
  );
}

function Toggle({ label, description, value, onChange, category }: ToggleConfig) {
  return (
    <label className="flex items-center gap-3 p-3 rounded-lg bg-white/2.5 border border-white/5 cursor-pointer hover:bg-white/5 transition-colors">
      <input
        type="checkbox"
        checked={value}
        onChange={e => onChange(e.target.checked)}
        className="w-4 h-4 rounded border-white/10 bg-white/5 text-indigo-500 focus:ring-indigo-500 focus:ring-2 appearance-none cursor-pointer"
      />
      <div className="flex-1">
        <span className="text-sm font-medium text-white">{label}</span>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${value ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-500/20 text-slate-500"}`}>
        {value ? "ON" : "OFF"}
      </span>
    </label>
  );
}

function MetricDisplay({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center p-3 rounded-xl bg-white/2.5 border border-white/5">
      <div className="text-2xl font-bold text-white tabular-nums">{value}</div>
      <div className="text-xs text-slate-500 uppercase tracking-wider">{label}</div>
    </div>
  );
}

function TelemetryGauge({ label, value, color, unit }: { label: string; value: number; color: string; unit: string }) {
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(value, 100) / 100) * circumference;

  const colorMap: Record<string, string> = {
    indigo: "#6366f1",
    emerald: "#22c55e",
    amber: "#f59e0b",
    cyan: "#06b6d4",
    violet: "#a855f7",
    rose: "#ef4444",
  };

  const strokeColor = colorMap[color] || colorMap.indigo;

  return (
    <div className="flex flex-col items-center gap-3 p-4 rounded-xl bg-white/2.5 border border-white/5">
      <svg width={96} height={96}>
        <circle
          cx={48}
          cy={48}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={6}
        />
        <circle
          cx={48}
          cy={48}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={6}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.5s ease, stroke 0.3s", transform: "rotate(-90deg)", transformOrigin: "48px 48px" }}
        />
      </svg>
      <div className="text-center">
        <div className="text-2xl font-bold text-white tabular-nums" style={{ color: strokeColor }}>
          {value}{unit}
        </div>
        <div className="text-xs text-slate-500 uppercase tracking-wider">{label}</div>
      </div>
    </div>
  );
}

function IntegrationCard({ integration, onToggle }: { integration: IntegrationConfig; onToggle: (id: string, enabled: boolean) => void }) {
  const statusColors = {
    connected: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    disconnected: "bg-slate-500/20 text-slate-400 border-slate-500/30",
    error: "bg-rose-500/20 text-rose-400 border-rose-500/30",
    pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  };

  const typeIcons = {
    api: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" /></svg>,
    database: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5v14c0 5.5 10 3 10 3s10-3 10-3V5" /><path d="M3 12c0 2.5 4 1.5 10 1.5s10-1.5 10-1.5" /></svg>,
    memory: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M6 2v20M18 2v20M6 2h12M6 22h12" /><path d="M6 8h12M6 14h12" /></svg>,
    service: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8M12 17v4" /></svg>,
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-white/2.5 border border-white/5">
      <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-white/5">
        {typeIcons[integration.type]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white truncate">{integration.name}</span>
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusColors[integration.status]}`}>
            {integration.status.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>{integration.type.toUpperCase()}</span>
          {integration.latency && <span>{integration.latency}ms latency</span>}
        </div>
      </div>
      <label className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={integration.status === "connected"}
          onChange={e => onToggle(integration.id, e.target.checked)}
          className="peer sr-only"
        />
        <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-500"></div>
      </label>
    </div>
  );
}

function AddIntegrationButton({ type, label, desc }: { type: string; label: string; desc: string }) {
  return (
    <button className="p-4 rounded-xl bg-white/2.5 border border-white/5 border-dashed text-left hover:bg-white/5 hover:border-indigo-500/50 transition-all">
      <div className="text-sm font-medium text-white">{label}</div>
      <div className="text-xs text-slate-500 mt-1">{desc}</div>
    </button>
  );
}