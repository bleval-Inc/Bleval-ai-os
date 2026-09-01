"use client";

import { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import BootSequence from "../components/boot/BootSequence";
import VoiceEngine from "../components/axiom/VoiceEngine";
import { ShellLayout } from "../components/shell/ShellLayout";

function getInitialBootState(): { bootComplete: boolean; hasBooted: boolean } {
  // Always return false,false for SSR safety to prevent hydration mismatch
  // Client-side useEffect will check sessionStorage and update state accordingly
  return { bootComplete: false, hasBooted: false };
}

export default function AppShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [bootComplete, setBootComplete] = useState(false);
  const [hasBooted, setHasBooted] = useState(false);

  // Check sessionStorage on client to optimize for returning users
  useEffect(() => {
    if (typeof window !== "undefined") {
      const booted = sessionStorage.getItem("axiom-booted");
      if (booted) {
        setBootComplete(true);
        setHasBooted(true);
      }
    }
  }, []);

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
          </ShellLayout>
        )}
      </AnimatePresence>
    </>
  );
}