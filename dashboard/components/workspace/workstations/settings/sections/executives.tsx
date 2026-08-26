"use client";

import { motion } from "framer-motion";
import { executives, type ExecutiveConfig } from "../settings-data";
import { SettingsPanel, ViewHeader, StatusPill } from "../settings-ui";

function Avatar({ e, size = 40 }: { e: ExecutiveConfig; size?: number }) {
  const initial = e.name.charAt(0);
  return (
    <div className="flex items-center justify-center rounded-xl text-white flex-shrink-0 relative overflow-hidden" style={{ width: size, height: size, background: e.gradient, boxShadow: `0 0 18px -3px ${e.accent}88` }}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
      <span className="relative text-base font-semibold">{initial}</span>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5 min-w-0">
      <span className="text-[9px] uppercase tracking-[0.14em] text-[var(--axiom-text-tertiary)]">{label}</span>
      <span className="text-[12px] text-[var(--axiom-text-primary)] leading-snug">{value}</span>
    </div>
  );
}

export default function ExecutivesView() {
  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="Executives"
        description="Agent configuration · communication · permission boundaries"
        right={<StatusPill label="3 online" tone="healthy" />}
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 items-start min-w-0">
        {executives.map((e, i) => (
          <motion.div key={e.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 + i * 0.06 }}>
            <SettingsPanel className="h-full">
              <div className="p-4 border-b" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
                <div className="flex items-center gap-3">
                  <Avatar e={e} />
                  <div className="min-w-0 flex-1">
                    <div className="text-[14px] font-semibold text-[var(--axiom-text-primary)]">{e.name}</div>
                    <div className="text-[10px] text-[var(--axiom-text-tertiary)]">{e.role}</div>
                  </div>
                  <StatusPill label={e.status} tone={e.status === "active" ? "active" : "neutral"} />
                </div>
              </div>

              <div className="p-4 space-y-3">
                <Field label="Communication" value={e.comms} />
                <Field label="Personality" value={e.personality} />
                <Field label="Behaviour" value={e.behaviour} />
                <div className="flex flex-col gap-1.5 pt-1 border-t" style={{ borderColor: "rgba(240,241,243,0.05)" }}>
                  <span className="text-[9px] uppercase tracking-[0.14em] text-[var(--axiom-text-tertiary)]">Permissions</span>
                  <div className="flex flex-wrap gap-1.5">
                    {e.permissions.map((p) => (
                      <span key={p} className="rounded-md px-2 py-0.5 text-[10px] text-[var(--axiom-text-secondary)]" style={{ borderColor: "rgba(109,124,255,0.16)", border: "1px solid rgba(109,124,255,0.16)", background: "rgba(109,124,255,0.05)" }}>
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </SettingsPanel>
          </motion.div>
        ))}
      </div>

      <SettingsPanel className="p-4">
        <p className="text-[11px] leading-relaxed text-[var(--axiom-text-tertiary)]">
          <span className="text-[var(--axiom-text-primary)] font-medium">Authority boundary: </span>
          Valta Prime may analyse, monitor, research, prepare, challenge, notify and coach — it cannot execute, modify or close trades. All agent behaviour is configuration placeholder data until live wiring.
        </p>
      </SettingsPanel>
    </div>
  );
}