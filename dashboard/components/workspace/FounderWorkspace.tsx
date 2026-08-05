"use client";

/**
 * @deprecated Phase E — WorkspaceShell now delegates to WorkstationRouter.
 * This file is kept for reference. The WorkstationRouter in ./WorkstationRouter.tsx
 * handles routing between all four workstations.
 *
 * TODO: Remove after Phase E stabilizes and no other component imports this.
 */

import CommandPalette from "./CommandPalette";
import WorkspaceSidebar from "./navigation/WorkspaceSidebar";
import WorkstationRouter from "./WorkstationRouter";

export default function WorkspaceShell() {
  return (
    <div className="flex-1 flex pt-10 h-screen overflow-hidden">
      <CommandPalette />
      <WorkspaceSidebar />
      <WorkstationRouter />
    </div>
  );
}