"use client";

import { useMemo, useState } from "react";
import { notificationToggles } from "../settings-data";
import { SettingsPanel, ViewHeader, Row, StatusPill, Toggle } from "../settings-ui";

const CHANNEL_LABEL: Record<string, string> = { push: "Push", email: "Email", sms: "SMS", voice: "Voice" };

export default function NotificationsView() {
  const [state, setState] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(notificationToggles.map((n) => [n.id, n.on])),
  );
  const onSum = useMemo(() => notificationToggles.filter((n) => state[n.id]).length, [state]);

  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="Notifications"
        description="Alerts, requests and escalation routing"
        right={<StatusPill label={`${onSum}/${notificationToggles.length} on`} tone="active" />}
      />

      <SettingsPanel>
        <div className="divide-y divide-[rgba(240,241,243,0.05)]">
          {notificationToggles.map((n) => (
            <Row
              key={n.id}
              label={n.label}
              desc={n.desc}
              right={
                <span className="flex items-center gap-3">
                  <span className="rounded-md px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-[var(--axiom-text-tertiary)]" style={{ background: "rgba(240,241,243,0.05)" }}>
                    {CHANNEL_LABEL[n.channel]}
                  </span>
                  <Toggle on={state[n.id]} onToggle={() => setState((s) => ({ ...s, [n.id]: !s[n.id] }))} />
                </span>
              }
            />
          ))}
        </div>
      </SettingsPanel>

      <SettingsPanel className="p-4">
        <p className="text-[11px] leading-relaxed text-[var(--axiom-text-tertiary)]">
          Emergency notifications route to the mobile + SMS escalation path regardless of the quiet-hours window. Channel delivery is a structural placeholder pending live notifier wiring.
        </p>
      </SettingsPanel>
    </div>
  );
}