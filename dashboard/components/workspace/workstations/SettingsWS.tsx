"use client";

import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { SettingsSectionId } from "./settings/types";
import { SettingsNav, SettingsNavBar } from "./settings/settings-nav";
import { Emblem } from "./settings/settings-ui";
import SystemView from "./settings/sections/SystemView";
import AIModelsView from "./settings/sections/aimodels";
import ExecutivesView from "./settings/sections/executives";
import FounderView from "./settings/sections/FounderView";
import VoiceView from "./settings/sections/VoiceView";
import NotificationsView from "./settings/sections/NotificationsView";
import IntegrationsView from "./settings/sections/IntegrationsView";
import SecurityView from "./settings/sections/SecurityView";
import AppearanceView from "./settings/sections/AppearanceView";

function SectionView({ section }: { section: SettingsSectionId }) {
  switch (section) {
    case "system": return <SystemView />;
    case "ai": return <AIModelsView />;
    case "executives": return <ExecutivesView />;
    case "founder": return <FounderView />;
    case "voice": return <VoiceView />;
    case "notifications": return <NotificationsView />;
    case "integrations": return <IntegrationsView />;
    case "security": return <SecurityView />;
    case "appearance": return <AppearanceView />;
  }
}

// SETTINGS — central configuration environment for the AXIOM AI OS.
// A premium desktop-OS section rail on small/large screens with the selected
// section's settings rendered in the main viewport. All destinations stay
// inside the Settings workstation. Frontend structure only — live wiring is a
// later step.
export default function SettingsWS() {
  const [section, setSection] = useState<SettingsSectionId>("system");
  const scrollRef = useRef<HTMLDivElement>(null);

  const select = (next: SettingsSectionId) => {
    setSection(next);
    scrollRef.current?.scrollTo({ top: 0 });
  };

  return (
    <div
      className="relative flex-1 min-h-0 overflow-hidden bg-[var(--axiom-bg-base)]"
      style={{
        background:
          "radial-gradient(ellipse 60% 45% at 0% 0%, rgba(109,124,255,0.05), transparent 60%), radial-gradient(ellipse 45% 40% at 100% 100%, rgba(168,140,255,0.05), transparent 60%), var(--axiom-bg-base)",
      }}
    >
      <div className="flex h-full min-w-0">
        {/* Left section rail — premium OS settings navigation */}
        <aside className="hidden lg:flex w-[260px] shrink-0 flex-col min-h-0 border-r" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
          <div className="flex items-center gap-3 px-4 h-16 border-b flex-shrink-0" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
            <Emblem />
            <div className="min-w-0">
              <div className="text-[12px] font-semibold text-[var(--axiom-text-primary)] leading-tight">AXIOM Settings</div>
              <div className="text-[9px] text-[var(--axiom-text-tertiary)]">Central configuration</div>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto hide-scrollbar p-2">
            <SettingsNav active={section} onSelect={select} />
          </div>
        </aside>

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Compact horizontal nav — narrow viewports */}
          <div className="lg:hidden flex-shrink-0 border-b" style={{ borderColor: "rgba(240,241,243,0.06)" }}>
            <SettingsNavBar active={section} onSelect={select} />
          </div>

          <section className="relative flex-1 min-h-0 overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={section}
                ref={scrollRef}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="absolute inset-0 overflow-y-auto hide-scrollbar p-5 md:p-7 pb-24"
              >
                <div className="min-h-full flex flex-col gap-4 min-w-0 mx-auto max-w-[1240px]">
                  <SectionView section={section} />
                </div>
              </motion.div>
            </AnimatePresence>
          </section>
        </div>
      </div>
    </div>
  );
}