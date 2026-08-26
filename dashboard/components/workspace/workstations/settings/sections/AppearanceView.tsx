"use client";

import { useState } from "react";
import { SettingsPanel, GroupTitle, ViewHeader, Row, Segmented, Toggle, StatusPill, Value } from "../settings-ui";

export default function AppearanceView() {
  const [theme, setTheme] = useState<"Dark" | "Darker" | "Light">("Dark");
  const [density, setDensity] = useState<"Comfortable" | "Compact">("Comfortable");
  const [animation, setAnimation] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [voiceUI, setVoiceUI] = useState(true);

  return (
    <div className="flex flex-col gap-4 min-w-0">
      <ViewHeader
        title="Appearance"
        description="Theme, density, motion and interface behaviour"
        right={<StatusPill label={theme} tone="active" />}
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start min-w-0">
        <div className="flex flex-col gap-4 min-w-0">
          <SettingsPanel>
            <GroupTitle title="Theme" />
            <div className="px-4 py-3.5">
              <Row label="Interface theme" right={<Segmented options={["Dark", "Darker", "Light"] as const} value={theme} onValue={setTheme} />} />
            </div>
          </SettingsPanel>

          <SettingsPanel>
            <GroupTitle title="Density" />
            <div className="px-4 py-3.5">
              <Row label="Interface density" desc="Controls spacing and row height" right={<Segmented options={["Comfortable", "Compact"] as const} value={density} onValue={setDensity} />} />
            </div>
          </SettingsPanel>

          <SettingsPanel>
            <GroupTitle title="Motion" />
            <div className="divide-y divide-[rgba(240,241,243,0.05)]">
              <Row label="Animation" desc="Animate transitions between surfaces" right={<Toggle on={animation} onToggle={() => setAnimation((v) => !v)} />} />
              <Row label="Reduced motion" desc="Minimise moving elements" right={<Toggle on={reducedMotion} onToggle={() => setReducedMotion((v) => !v)} />} />
            </div>
          </SettingsPanel>
        </div>

        <div className="flex flex-col gap-4 min-w-0">
          <SettingsPanel>
            <GroupTitle title="Interface" />
            <div className="divide-y divide-[rgba(240,241,243,0.05)]">
              <Row label="Voice interface" desc="Voice control across workstations" right={<Toggle on={voiceUI} onToggle={() => setVoiceUI((v) => !v)} />} />
              <Row label="Workstation behaviour" desc="Persist last open view per workstation" right={<Value>Persist views</Value>} />
            </div>
          </SettingsPanel>

          <SettingsPanel className="p-4">
            <p className="text-[11px] leading-relaxed text-[var(--axiom-text-tertiary)]">
              Appearance controls apply to the AXIOM interface shell. Selecting a theme and density is local placeholder behaviour until the global theme system is connected.
            </p>
          </SettingsPanel>
        </div>
      </div>
    </div>
  );
}