"use client";

import { cn } from "@/lib/utils";
import { SETTINGS_SECTIONS, type SettingsSectionMeta } from "./settings-data";
import { Glyph } from "./settings-ui";
import type { SettingsSectionId } from "./types";

const ACTIVE_BG = "linear-gradient(135deg,#6d7cff,#a88cff)";

function NavButton({ s, active, onSelect }: { s: SettingsSectionMeta; active: boolean; onSelect: (id: SettingsSectionId) => void }) {
  return (
    <button
      onClick={() => onSelect(s.id)}
      aria-pressed={active}
      title={s.label}
      className={cn(
        "group flex items-center gap-3 w-full rounded-xl px-3 py-2.5 text-left transition-colors",
        active ? "text-white" : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)] hover:bg-[var(--axiom-bg-glass-hover)]",
      )}
      style={active ? { background: ACTIVE_BG, boxShadow: "0 0 18px -4px rgba(109,124,255,0.5)" } : { background: "transparent" }}
    >
      <span className={cn("flex-shrink-0 flex items-center justify-center", active ? "" : "opacity-80 group-hover:opacity-100")}>
        <Glyph name={s.icon} size={16} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[12px] font-medium leading-tight truncate">{s.label}</span>
        <span className={cn("block text-[9px] leading-tight truncate mt-0.5", active ? "text-white/70" : "text-[var(--axiom-text-tertiary)]/70")}>{s.description}</span>
      </span>
    </button>
  );
}

// Left-hand section rail (premium desktop-OS settings navigation). On small
// screens the container renders the horizontal variant instead.
export function SettingsNav({ active, onSelect }: { active: SettingsSectionId; onSelect: (id: SettingsSectionId) => void }) {
  return (
    <nav className="flex flex-col gap-1 p-2 min-w-0" aria-label="Settings sections">
      {SETTINGS_SECTIONS.map((s) => <NavButton key={s.id} s={s} active={active === s.id} onSelect={onSelect} />)}
    </nav>
  );
}

// Compact horizontal variant for narrow viewports / the shell.
export function SettingsNavBar({ active, onSelect }: { active: SettingsSectionId; onSelect: (id: SettingsSectionId) => void }) {
  return (
    <nav className="flex items-center gap-1 overflow-x-auto hide-scrollbar px-3 py-2.5" aria-label="Settings sections">
      {SETTINGS_SECTIONS.map((s) => {
        const isActive = active === s.id;
        return (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            aria-pressed={isActive}
            className={cn("flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-semibold whitespace-nowrap transition-colors flex-shrink-0", isActive ? "text-white" : "text-[var(--axiom-text-tertiary)] hover:text-[var(--axiom-text-primary)]")}
            style={isActive ? { background: ACTIVE_BG } : { background: "rgba(10,12,16,0.4)", border: "1px solid rgba(240,241,243,0.08)" }}
          >
            <Glyph name={s.icon} size={13} />
            {s.label}
          </button>
        );
      })}
    </nav>
  );
}