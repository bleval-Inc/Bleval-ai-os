"use client";

import { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import BootSequence from "../components/boot/BootSequence";
import VoiceEngine from "../components/axiom/VoiceEngine";
import SystemTelemetry from "../components/axiom/SystemTelemetry";
import { ShellLayout } from "../components/shell/ShellLayout";

function getInitialBootState(): { bootComplete: boolean; hasBooted: boolean } {
  if (typeof window !== "undefined") {
    const booted = sessionStorage.getItem("axiom-booted");
    if (booted) {
      return { bootComplete: true, hasBooted: true };
    }
  }
  return { bootComplete: false, hasBooted: false };
}

export default function AppShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [bootComplete, setBootComplete] = useState(() => getInitialBootState().bootComplete);
  const [hasBooted, setHasBooted] = useState(() => getInitialBootState().hasBooted);

  const handleBootComplete = () => {
    setBootComplete(true);
    sessionStorage.setItem("axiom-booted", "true");
    setTimeout(() => setHasBooted(true), 800);
  };

  // Initialize voice engine and telemetry after boot
  useEffect(() => {
    if (hasBooted) {
      // These components will self-initialize
    }
  }, [hasBooted]);

  return (
    <>
      {/* Boot Sequence */}
      {!bootComplete && <BootSequence onComplete={handleBootComplete} />}

      {/* OS Interface */}
      <AnimatePresence>
        {hasBooted && (
          <ShellLayout>
            {children}
            <VoiceEngine />
            <SystemTelemetry />
          </ShellLayout>
        )}
      </AnimatePresence>
    </>
  );
}