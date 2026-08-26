"use client";

import { aiActiveModel, executiveModels, modelParameters, aiApiConfig } from "../settings-data";
import { SettingsPanel, GroupTitle, ViewHeader, Row, Value, StatusPill } from "../settings-ui";

export default function AIModelsView() {
  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="AI & Models"
        description="Active models, provider configuration and inference parameters"
        right={<StatusPill label="Providers configured" tone="active" />}
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start min-w-0">
        {/* Left column */}
        <div className="flex flex-col gap-4 min-w-0">
          <SettingsPanel>
            <GroupTitle title="AXIOM active model" />
            <div className="px-4 py-3 flex flex-wrap items-center gap-3">
              <span className="w-9 h-9 rounded-xl flex items-center justify-center text-white" style={{ background: "linear-gradient(135deg,#6d7cff,#a88cff)", boxShadow: "0 0 16px -3px rgba(109,124,255,0.5)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l1.7 4.4L18 9l-4.3 1.6L12 15l-1.7-4.4L6 9l4.3-1.6z" /></svg>
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-[13px] font-medium text-[var(--axiom-text-primary)]">{aiActiveModel.name}</div>
                <div className="text-[10px] text-[var(--axiom-text-tertiary)]">{aiActiveModel.desc}</div>
              </div>
              <StatusPill label="Active" tone="active" />
            </div>
          </SettingsPanel>

          <SettingsPanel>
            <GroupTitle title="Executive models" hint="Per-executive assignment" />
            <div className="divide-y divide-[rgba(240,241,243,0.04)]">
              {executiveModels.map((m) => (
                <Row key={m.id} label={m.label} desc={m.desc} right={<Value mono>{m.value}</Value>} />
              ))}
            </div>
          </SettingsPanel>

          <SettingsPanel>
            <GroupTitle title="Model parameters" />
            <div className="divide-y divide-[rgba(240,241,243,0.04)]">
              {modelParameters.map((p) => (
                <Row key={p.id} label={p.label} desc={p.desc} right={<Value mono>{p.value}</Value>} />
              ))}
            </div>
          </SettingsPanel>
        </div>

        {/* Right column — provider + API config */}
        <div className="flex flex-col gap-4 min-w-0">
          <SettingsPanel>
            <GroupTitle title="Model provider" />
            <div className="divide-y divide-[rgba(240,241,243,0.04)]">
              {aiApiConfig.map((a) => (
                <Row key={a.id} label={a.label} desc={a.desc} right={<Value mono>{a.value}</Value>} />
              ))}
            </div>
          </SettingsPanel>
          <SettingsPanel className="p-4">
            <p className="text-[11px] leading-relaxed text-[var(--axiom-text-tertiary)]">
              New model integrations are intentionally not yet connected. The provider and parameter surfaces above are structural placeholders for live wiring in a later step.
            </p>
          </SettingsPanel>
        </div>
      </div>
    </div>
  );
}