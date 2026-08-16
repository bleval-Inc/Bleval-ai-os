"use client";

import { useEffect } from "react";
import { useAxiomStore } from "@/lib/store/axiom-store";
import WorkstationRouter from "@/components/workspace/WorkstationRouter";

export default function SystemPage() {
  const { setActiveWorkstation, setActiveView } = useAxiomStore();

  useEffect(() => {
    setActiveWorkstation("system");
    setActiveView("system");
  }, [setActiveWorkstation, setActiveView]);

  return <WorkstationRouter />;
}