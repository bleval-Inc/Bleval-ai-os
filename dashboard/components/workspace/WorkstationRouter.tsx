"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useAxiomStore, type WorkstationId } from "../../lib/store/axiom-store";
import AXIOMWS from "./workstations/AXIOMWS";
import BLEVALINCWorkstation from "./workstations/bleval/BLEVALINCWorkstation";
import VALTAWS from "./workstations/VALTAWS";
import PERSONALWS from "./workstations/PERSONALWS";
import BoardroomWS from "./workstations/BoardroomWS";
import SystemWS from "./workstations/SystemWS";

const pageVariants = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.2, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" as const } },
};

const WORKSTATION_MAP: Partial<Record<WorkstationId, React.FC>> = {
  axiom: AXIOMWS,
  bleval: BLEVALINCWorkstation,
  valta: VALTAWS,
  personal: PERSONALWS,
  boardroom: BoardroomWS,
  system: SystemWS,
};

export default function WorkstationRouter() {
  const activeWorkstation = useAxiomStore((s) => s.activeWorkstation);
  // Fall back to AXIOM if the store holds a key that isn't a valid workstation
  // (e.g. the "workspace" home view). This guarantees the router never tries
  // to render an undefined element (React error #130).
  const W = WORKSTATION_MAP[activeWorkstation] ?? AXIOMWS;

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