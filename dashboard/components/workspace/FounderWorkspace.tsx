"use client";

import CommandPalette from "./CommandPalette";
import WorkstationRouter from "./WorkstationRouter";

export default function WorkspaceShell() {
  return (
    <div className="flex-1 flex h-screen overflow-hidden">
      <CommandPalette />
      <WorkstationRouter />
    </div>
  );
}