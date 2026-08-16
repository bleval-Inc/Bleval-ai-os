"use client";

import { useEffect } from "react";
import { useAxiomStore } from "@/lib/store/axiom-store";
import WorkstationRouter from "@/components/workspace/WorkstationRouter";

export default function BlevalPage() {
  const { setActiveWorkstation, setActiveView } = useAxiomStore();

  useEffect(() => {
    setActiveWorkstation("bleval");
    setActiveView("workspace");
  }, [setActiveWorkstation, setActiveView]);

  return <WorkstationRouter />;
}