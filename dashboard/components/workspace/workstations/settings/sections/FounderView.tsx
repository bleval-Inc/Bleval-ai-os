"use client";

import { motion } from "framer-motion";
import { authorityRules, authorityLevelMeta } from "../settings-data";
import { SettingsPanel, GroupTitle, ViewHeader, StatusPill } from "../settings-ui";
import type { AuthorityLevel } from "../settings-data";

export default function FounderView() {
  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="Founder"
        description="Approval rules and the boundaries of agent authority"
        right={<StatusPill label="All boundaries enforced" tone="warning" />}
      />

      <SettingsPanel className="p-4" >
        <p className="text-[11px] leading-relaxed text-[var(--axiom-text-tertiary)]">
          No executive holds authority to execute, modify or close trades, make irreversible changes, or spend without founder approval. Boundaries are enforced by the gatekeeper at the AXIOM system boundary.
        </p>
      </SettingsPanel>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start min-w-0">
        {authorityRules.map((rule, i) => {
          const meta = authorityLevelMeta[rule.level];
          return (
            <motion.div key={rule.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 + i * 0.05 }}>
              <SettingsPanel className="h-full">
                <GroupTitle title={rule.label} hint={rule.desc} />
                <div className="px-4 py-3 flex items-center justify-between gap-3">
                  <span className="text-[11px] text-[var(--axiom-text-secondary)]">{rule.desc}</span>
                  <StatusPill label={meta.label} tone={meta.tone} />
                </div>
              </SettingsPanel>
            </motion.div>
          );
        })}
      </div>

      <SettingsPanel className="p-3.5" >
        <div className="flex items-start gap-2.5">
          <StatusPill label="LOCK" tone="danger" dot={false} />
          <p className="text-[11px] leading-relaxed text-[var(--axiom-text-secondary)]">
            Irreversible actions (deletes, overwrites, permanent config changes) require a second confirmation and are logged to the audit trail.
          </p>
        </div>
      </SettingsPanel>
    </div>
  );
}

export type { AuthorityLevel };