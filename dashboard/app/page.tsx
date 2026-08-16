"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import BLEVALConsole from "@/components/dashboard/BLEVALConsole";
import ValtaConsole from "@/components/dashboard/ValtaConsole";
import PersonalConsole from "@/components/dashboard/PersonalConsole";
import AxiomSystemConsole from "@/components/dashboard/AxiomSystemConsole";

export default function HomeDashboard() {
  const router = useRouter();

  const handleLogoClick = () => {
    // Navigate to the AXIOM AI Workstation inside the existing OS shell (SPA navigation).
    router.push("/axiom");
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[var(--axiom-bg-base)]">
      {/* Page content - full viewport centered layout */}
      <main className="flex-1 min-h-0 overflow-y-auto">
        <div className="w-full max-w-[120rem] mx-auto p-6 md:p-8">
          {/* AXIOM AI Workstation entrance - compact emblem */}
          <div className="flex justify-center mb-6">
            <motion.button
              onClick={handleLogoClick}
              className="group flex items-center gap-3 px-5 py-2.5 rounded-2xl cursor-pointer"
              style={{
                background: "linear-gradient(135deg, var(--axiom-bg-elevated) 0%, var(--axiom-bg-surface) 100%)",
                border: "1px solid var(--axiom-border)",
                boxShadow: "0 0 30px -10px rgba(99,102,241,0.35), inset 0 1px 0 rgba(255,255,255,0.05)"
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              aria-label="Open AXIOM AI Workstation"
            >
              <span className="w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-[var(--axiom-accent)] to-[var(--axiom-violet)]">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
              </span>
              <span className="text-xs font-semibold tracking-widest uppercase text-[var(--axiom-text-primary)]">AXIOM AI Workstation</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--axiom-accent)] transition-transform duration-200 group-hover:translate-x-0.5">
                <path d="M5 12h14" /><polyline points="12 5 19 12 12 19" />
              </svg>
            </motion.button>
          </div>

          {/* Workstation cards - strict 2x2 grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* BLEVAL INC premium console */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="min-w-0 h-[560px]"
            >
              <BLEVALConsole />
            </motion.div>

            {/* HOUSE OF VALTA premium console */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.05, ease: "easeOut" }}
              className="min-w-0 h-[560px]"
            >
              <ValtaConsole />
            </motion.div>

            {/* PERSONAL premium console */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
              className="min-w-0 h-[560px]"
            >
              <PersonalConsole />
            </motion.div>

            {/* AXIOM SYSTEM premium console */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.15, ease: "easeOut" }}
              className="min-w-0 h-[560px]"
            >
              <AxiomSystemConsole />
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}