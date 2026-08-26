"use client";

import { motion } from "framer-motion";
import { integrations, type Integration } from "../settings-data";
import { SettingsPanel, ViewHeader, StatusPill } from "../settings-ui";

const CHANNEL_GLYPH: Record<string, React.ReactNode> = {
  mail: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></>,
  sms: <><path d="M21 4H3v13h5l3 3 3-3h7z" /><path d="M8 13h.01M12 13h.01M16 13h.01" /></>,
  calendar: <><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></>,
  social: <><circle cx="12" cy="12" r="3" /><path d="M12 8.5V7M12 17v-1.5M8.5 12H7M17 12h-1.5M9.9 9.9L8.8 8.8M15.2 15.2l-1.1-1.1M14.1 9.9l1.1-1.1M8.8 15.2l1.1-1.1" /></>,
  git: <><circle cx="9" cy="5" r="2" /><circle cx="15" cy="12" r="2" /><circle cx="9" cy="19" r="2" /><path d="M11 6.5l2 3.5M11 17.5l2-3.5" /></>,
  data: <><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" /></>,
};

const integrationTone = (s: Integration["status"]) =>
  s === "connected" ? "healthy" : s === "setup" ? "warning" : "neutral";

export default function IntegrationsView() {
  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="Integrations"
        description="Connected services. New integrations are not yet wired."
        right={<StatusPill label="3 connected" tone="warning" />}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 min-w-0">
        {integrations.map((it, i) => (
          <motion.div key={it.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.06 + i * 0.05 }}>
            <SettingsPanel className="h-full">
              <div className="p-4 flex flex-col gap-3 min-w-0">
                <div className="flex items-center gap-3">
                  <span className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: "rgba(109,124,255,0.08)", border: "1px solid rgba(109,124,255,0.16)", color: "#a8b3ff" }}>
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">{CHANNEL_GLYPH[it.channel]}</svg>
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] font-medium text-[var(--axiom-text-primary)] truncate">{it.name}</div>
                    <div className="text-[10px] text-[var(--axiom-text-tertiary)] truncate">{it.provider}</div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-[var(--axiom-text-tertiary)]">{it.provider === "—" ? "No provider configured" : "Provider"}</span>
                  <StatusPill label={it.status === "connected" ? "Connected" : it.status === "setup" ? "Setup pending" : "Not connected"} tone={integrationTone(it.status)} />
                </div>
              </div>
            </SettingsPanel>
          </motion.div>
        ))}
      </div>
    </div>
  );
}