"use client";

import { securityRows } from "../settings-data";
import { SettingsPanel, GroupTitle, ViewHeader, Row, Value, StatusPill } from "../settings-ui";

export default function SecurityView() {
  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="Security"
        description="Authentication, sessions, permissions and audit"
        right={<StatusPill label="Protected" tone="healthy" />}
      />

      <SettingsPanel>
        <GroupTitle title="Security posture" hint="Live placeholders" />
        <div className="divide-y divide-[rgba(240,241,243,0.04)]">
          {securityRows.map((s) => (
            <Row key={s.id} label={s.label} right={<Value mono>{s.value}</Value>} />
          ))}
        </div>
      </SettingsPanel>

      <SettingsPanel className="p-4">
        <p className="text-[11px] leading-relaxed text-[var(--axiom-text-tertiary)]">
          Real credentials are never displayed — API keys and secrets are masked and rotated. Authentication and session controls are structural placeholders for live hardening in a later step.
        </p>
      </SettingsPanel>
    </div>
  );
}