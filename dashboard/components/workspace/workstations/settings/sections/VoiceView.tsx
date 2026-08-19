"use client";

import { voiceConfig, executiveVoices, voiceArbitration } from "../settings-data";
import { SettingsPanel, GroupTitle, ViewHeader, Row, Value, StatusPill } from "../settings-ui";

export default function VoiceView() {
  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="Voice"
        description="Microphone, voice engines, wake words and arbitration"
        right={<StatusPill label="Engine ready" tone="active" />}
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start min-w-0">
        <SettingsPanel>
          <GroupTitle title="Speech & wake" />

          <div className="divide-y divide-[rgba(240,241,243,0.04)]">
            {voiceConfig.map((v) => (
              <Row key={v.id} label={v.label} right={<Value mono>{v.value}</Value>} />
            ))}
          </div>

          <div className="px-4 py-3.5 border-t" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
            <span className="text-[9px] uppercase tracking-[0.14em] text-[var(--axiom-text-tertiary)] mb-1 block">Voice arbitration</span>
            <p className="text-[11px] leading-snug text-[var(--axiom-text-secondary)]">{voiceArbitration}</p>
          </div>
        </SettingsPanel>

        <div className="flex flex-col gap-4 min-w-0">
          <SettingsPanel>
            <GroupTitle title="Executive voices" hint="Per-executive engine" />
            <div className="divide-y divide-[rgba(240,241,243,0.04)]">
              {executiveVoices.map((v) => (
                <Row key={v.id} label={v.label} right={<Value>{v.value}</Value>} />
              ))}
            </div>
          </SettingsPanel>

          <SettingsPanel className="p-4">
            <p className="text-[11px] leading-relaxed text-[var(--axiom-text-tertiary)]">
              Speech settings surface reserved for live microphone and engine wiring in a later step. Wake-word recognition is enabled structurally only.
            </p>
          </SettingsPanel>
        </div>
      </div>
    </div>
  );
}