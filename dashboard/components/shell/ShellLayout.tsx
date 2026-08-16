"use client";

import { useAxiomStore } from "../../lib/store/axiom-store";
import { GlobalTopNavigation } from "./GlobalTopNavigation";
import { GlobalLeftSidebar } from "./GlobalLeftSidebar";
import { Dock } from "./components/Dock";

/**
 * Axiom AI OS global shell frame.
 * Owns the three fixed core regions (Top Navigation, Collapsible Left Sidebar,
 * Floating Action Dock) plus the mounted voice/telemetry overlays. Rendered as
 * the wrapper inside the app root layout so every view inherits the OS frame.
 * Dock only renders in BLEVAL, VALTA, and PERSONAL workstations.
 */
export function ShellLayout({ children }: { children: React.ReactNode }) {
  const activeWorkstation = useAxiomStore((s) => s.activeWorkstation);
  const showDock = ["bleval", "valta", "personal"].includes(activeWorkstation);

  return (
    <>
      <div className="fixed inset-0 flex flex-col">
        {/* A. Top Navigation Bar */}
        <GlobalTopNavigation />

        {/* Main Content Area */}
        <div className="flex-1 flex min-h-0">
          {/* B. Collapsible Left Sidebar */}
          <GlobalLeftSidebar />

          {/* Workspace Content */}
          <main className="flex-1 flex min-w-0 overflow-hidden">
            {children}
          </main>
        </div>
      </div>

      {/* C. Bottom Floating Action Dock — only in BLEVAL/VALTA/PERSONAL */}
      {showDock && <Dock />}
    </>
  );
}

export default ShellLayout;