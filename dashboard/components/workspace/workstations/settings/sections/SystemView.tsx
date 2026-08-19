"use client";

import { systemStatus, systemHealth, systemStacks } from "../settings-data";
import { SettingsPanel, GroupTitle, ViewHeader, Row, Value, StatusPill, Meter } from "../settings-ui";
import { SETTING_SUCCESS } from "../types";

export default function SystemView() {
  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="System"
        description="AXIOM OS configuration, runtime health and services"
        right={<StatusPill label="Operational" tone="healthy" />}
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start min-w-0">
        {/* Left column */}
        <div className="flex flex-col gap-4 min-w-0">
          <SettingsPanel>
            <GroupTitle title="System status" />
            <div className="divide-y divide-[rgba(240,241,243,0.04)]">
              {systemStatus.map((s) => (
                <Row key={s.label} label={s.label} right={<Value mono>{s.value}</Value>} />
              ))}
            </div>
          </SettingsPanel>

          <SettingsPanel>
            <GroupTitle title="Runtime health" hint="Current load" />
            <div className="px-4 py-2">
              {systemHealth.map((m) => (
                <Row key={m.label} label={m.label} right={<Meter value={m.value} color={m.value > 80 ? "#ffb830" : SETTING_SUCCESS} />} />
              ))}
            </div>
          </SettingsPanel>
        </div>

        {/* Right column — engines, workflows, agents, services */}
        <div className="flex flex-col gap-4 min-w-0">
          {systemStacks.map((stack) => (
            <SettingsPanel key={stack.title}>
              <GroupTitle title={stack.title} />
              <div className="px-4 py-3 flex flex-wrap gap-2">
                {stack.items.map((item) => (
                  <span key={item} className="rounded-lg border px-2.5 py-1 text-[11px] text-[var(--axiom-text-secondary)]" style={{ borderColor: "rgba(109,124,255,0.14)", background: "rgba(109,124,255,0.04)" }}>
                    {item}
                  </span>
                ))}
              </div>
            </SettingsPanel>
          ))}
        </div>
      </div>
    </div>
  );
}