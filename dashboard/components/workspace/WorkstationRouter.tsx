"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore, type WorkstationId } from "../../lib/store/axiom-store";
import AXIOMWS from "./workstations/AXIOMWS";
import BLEVALWS from "./workstations/BLEVALWS";
import VALTAWS from "./workstations/VALTAWS";
import PERSONALWS from "./workstations/PERSONALWS";

const pageVariants = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.2, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" as const } },
};

const WORKSTATION_MAP: Record<WorkstationId, React.FC> = {
  axiom: AXIOMWS,
  bleval: BLEVALWS,
  valta: VALTAWS,
  personal: PERSONALWS,
};

export default function WorkstationRouter() {
  const activeWorkstation = useAxiomStore((s) => s.activeWorkstation);
  const W = WORKSTATION_MAP[activeWorkstation];

  return (
    <div className="flex-1 flex overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.div
          key={activeWorkstation}
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          className="flex-1 flex overflow-hidden"
        >
          <W />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}