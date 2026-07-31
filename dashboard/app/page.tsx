"use client";

import { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import BootSequence from "../components/boot/BootSequence";
import StatusBar from "../components/runtime/StatusBar";
import VoiceEngine from "../components/axiom/VoiceEngine";
import SystemTelemetry from "../components/axiom/SystemTelemetry";
import WorkspaceShell from "../components/workspace/FounderWorkspace";

export default function Home() {
  const [bootComplete, setBootComplete] = useState(false);
  const [hasBooted, setHasBooted] = useState(false);

  // Check if user has already booted this session
  useEffect(() => {
    const booted = sessionStorage.getItem("axiom-booted");
    if (booted) {
      setBootComplete(true);
      setHasBooted(true);
    }
  }, []);

  const handleBootComplete = () => {
    setBootComplete(true);
    sessionStorage.setItem("axiom-booted", "true");
    // Delay to let boot animations finish
    setTimeout(() => setHasBooted(true), 800);
  };

  return (
    <>
      {/* Boot Sequence */}
      {!bootComplete && (
        <BootSequence onComplete={handleBootComplete} />
      )}

      {/* OS Interface */}
      <AnimatePresence>
        {hasBooted && (
          <>
            <StatusBar />
            <WorkspaceShell />
            <VoiceEngine />
            <SystemTelemetry />
          </>
        )}
      </AnimatePresence>
    </>
  );
}